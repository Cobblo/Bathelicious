from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

import datetime
import json
import razorpay

from carts.models import CartItem
from store.models import Product
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from .utils import send_invoice_email
from django.templatetags.static import static
from orders.utils import calculate_shipping_charge

# ---------- Shipping policy ----------
FREE_SHIPPING_THRESHOLD = Decimal('999')   # Free at ₹999 and above
# If you want to keep a central rate in calculate_shipping_charge(),
# leave it there and we’ll only use it when total < threshold.


# STEP 1: PLACE ORDER & CREATE RAZORPAY ORDER
@login_required
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user, is_active=True)
    if cart_items.count() <= 0:
        return redirect('store')

    # ---- compute totals (no tax) ----
    total = Decimal('0')
    quantity = 0
    for item in cart_items:
        # assuming Product.price is a DecimalField
        total += (item.product.price * item.quantity)
        quantity += item.quantity

    # shipping: Free if total >= 999, else use your per-state function (usually ₹80)
    # we need state from the submitted form to compute a per-state rate;
    # until form is submitted, show the flat policy on the next page.
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # No tax
            tax = Decimal('0')

            # Determine shipping charge
            # If you want a *strict* ₹80 below threshold, replace the next line with:
            # shipping_charge = Decimal('0') if total >= FREE_SHIPPING_THRESHOLD else Decimal('80')
            shipping_charge = Decimal('0') if total >= FREE_SHIPPING_THRESHOLD else Decimal('80')

            grand_total = (total + shipping_charge).quantize(Decimal('1.00'))

            # ---- Save Order (not yet ordered) ----
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.pincode = form.cleaned_data['pincode']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.shipping_charge = shipping_charge
            data.tax = tax  # keep field for compatibility, value is 0
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number: YYYYMMDD + id
            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            # ---- Razorpay Order ----
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_paise = int((grand_total * 100).to_integral_value())  # paise

            razorpay_order = client.order.create({
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': '1'
            })

            data.razorpay_order_id = razorpay_order['id']
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,  # always 0 now
                'shipping': shipping_charge,
                'grand_total': grand_total,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'razorpay_amount': amount_paise,  # integer paise
            }
            return render(request, 'orders/payments.html', context)
        else:
            # invalid form -> back to checkout
            return redirect('checkout')
    else:
        # Only accept POST to create the order
        return redirect('checkout')


# STEP 2: HANDLE PAYMENT RESPONSE & SAVE ORDER
@login_required
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,  # this is total + shipping (no tax)
        status=body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order = order
        orderproduct.payment = payment
        orderproduct.user = request.user
        orderproduct.product = item.product
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # Set variations
        orderproduct.variations.set(item.variations.all())
        orderproduct.save()

        # Decrease stock
        product = item.product
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


# STEP 3: ORDER COMPLETE PAGE
def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = sum(item.product_price * item.quantity for item in ordered_products)
        payment = Payment.objects.get(payment_id=transID)
        send_invoice_email(order, payment, ordered_products)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'shipping': order.shipping_charge,
            # no tax shown here either; if template expects it, it will be 0 from order.tax
        }
        return render(request, 'orders/order_complete.html', context)
    except (Order.DoesNotExist, Payment.DoesNotExist):
        return redirect('home')


@login_required
def order_status(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_status.html', {'orders': orders})
