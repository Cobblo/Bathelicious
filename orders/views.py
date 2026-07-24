from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

import datetime
import json
import razorpay

from carts.models import CartItem
from store.models import Coupon, CouponUsage, Product

from .forms import OrderForm
from .models import Order, OrderProduct, Payment
from .utils import send_invoice_email


# ---------- Offer policies ----------
FREE_SHIPPING_THRESHOLD = Decimal("1199.00")
TEN_PERCENT_OFFER_THRESHOLD = Decimal("2499.00")
TEN_PERCENT_OFFER_RATE = Decimal("0.10")


def calculate_offer_discount(total):
    """
    Automatically applies a 10% discount when the product total
    is ₹2,499 or more.
    """
    if total >= TEN_PERCENT_OFFER_THRESHOLD:
        return (
            total * TEN_PERCENT_OFFER_RATE
        ).quantize(Decimal("0.01"))

    return Decimal("0.00")


@login_required
def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(
        user=current_user,
        is_active=True
    )

    if cart_items.count() <= 0:
        return redirect("store")

    total = Decimal("0.00")
    quantity = 0
    discount = Decimal("0.00")
    offer_discount = Decimal("0.00")
    coupon = None
    returning_customer_discount = Decimal("0.00")

    previous_paid_order = Order.objects.filter(
        user=current_user,
        is_ordered=True
    ).exists()

    already_used = Order.objects.filter(
        user=current_user,
        returning_discount_used=True
    ).exists()

    if previous_paid_order and not already_used:
        returning_customer_discount = Decimal("100.00")

    for item in cart_items:
        total += (
            Decimal(str(item.product.price))
            * item.quantity
        )

        quantity += item.quantity

    offer_discount = calculate_offer_discount(total)

    # Temporary - Free shipping for testing
    shipping_charge = Decimal("0.00")

    coupon_id = request.session.get("coupon_id")

    if coupon_id:
        try:
            coupon = Coupon.objects.get(
                id=coupon_id,
                is_active=True
            )

            is_valid, message, discount = (
                coupon.validate_coupon(
                    user=current_user,
                    cart_items=cart_items,
                    Order=Order
                )
            )

            if not is_valid:
                request.session.pop(
                    "coupon_id",
                    None
                )

                coupon = None
                discount = Decimal("0.00")

        except Coupon.DoesNotExist:
            request.session.pop(
                "coupon_id",
                None
            )

            coupon = None
            discount = Decimal("0.00")

    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
            tax = Decimal("0.00")

            grand_total = (
                total
                + shipping_charge
                - discount
                - returning_customer_discount
                - offer_discount
            ).quantize(Decimal("0.01"))

            if grand_total < Decimal("0.00"):
                grand_total = Decimal("0.00")

            total_discount_amount = (
                discount
                + returning_customer_discount
                + offer_discount
            ).quantize(Decimal("0.01"))

            data = Order()

            data.user = current_user
            data.first_name = form.cleaned_data["first_name"]
            data.last_name = form.cleaned_data["last_name"]
            data.phone = form.cleaned_data["phone"]
            data.email = form.cleaned_data["email"]
            data.address_line_1 = form.cleaned_data[
                "address_line_1"
            ]
            data.address_line_2 = form.cleaned_data[
                "address_line_2"
            ]
            data.pincode = form.cleaned_data["pincode"]
            data.state = form.cleaned_data["state"]
            data.city = form.cleaned_data["city"]
            data.order_note = form.cleaned_data["order_note"]

            data.order_total = float(grand_total)
            data.shipping_charge = shipping_charge
            data.discount_amount = total_discount_amount
            data.coupon_code = coupon.code if coupon else ""
            data.tax = float(tax)
            data.ip = request.META.get("REMOTE_ADDR")

            data.save()

            current_date = datetime.date.today().strftime(
                "%Y%m%d"
            )

            order_number = current_date + str(data.id)

            data.order_number = order_number
            data.save()

            client = razorpay.Client(
                auth=(
                    settings.RAZORPAY_KEY_ID,
                    settings.RAZORPAY_KEY_SECRET
                )
            )

            amount_paise = int(
                (
                    grand_total * Decimal("100")
                ).to_integral_value()
            )

            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": "1"
            })

            data.razorpay_order_id = razorpay_order["id"]
            data.save()

            order = Order.objects.get(
                user=current_user,
                is_ordered=False,
                order_number=order_number
            )

            context = {
                "order": order,
                "cart_items": cart_items,
                "total": total,
                "tax": tax,
                "shipping": shipping_charge,
                "discount": discount,
                "offer_discount": offer_discount,
                "returning_customer_discount": (
                    returning_customer_discount
                ),
                "total_discount_amount": (
                    total_discount_amount
                ),
                "coupon": coupon,
                "grand_total": grand_total,
                "original_total": (
                    total + shipping_charge
                ),
                "razorpay_order_id": (
                    razorpay_order["id"]
                ),
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "razorpay_amount": amount_paise,
            }

            return render(
                request,
                "orders/payments.html",
                context
            )

        grand_total = (
            total
            + shipping_charge
            - discount
            - returning_customer_discount
            - offer_discount
        ).quantize(Decimal("0.01"))

        if grand_total < Decimal("0.00"):
            grand_total = Decimal("0.00")

        context = {
            "form": form,
            "total": total,
            "quantity": quantity,
            "cart_items": cart_items,
            "shipping": shipping_charge,
            "discount": discount,
            "offer_discount": offer_discount,
            "returning_customer_discount": (
                returning_customer_discount
            ),
            "coupon": coupon,
            "original_total": (
                total + shipping_charge
            ),
            "grand_total": grand_total,
        }

        return render(
            request,
            "store/checkout.html",
            context
        )

    return redirect("checkout")


@login_required
def payments(request):
    body = json.loads(request.body)

    order = Order.objects.get(
        user=request.user,
        is_ordered=False,
        order_number=body["orderID"]
    )

    payment = Payment(
        user=request.user,
        payment_id=body["transID"],
        payment_method=body["payment_method"],
        amount_paid=order.order_total,
        status=body["status"],
    )

    payment.save()

    order.payment = payment
    order.is_ordered = True

    previous_discount_used = Order.objects.filter(
        user=request.user,
        returning_discount_used=True
    ).exists()

    previous_orders = Order.objects.filter(
        user=request.user,
        is_ordered=True
    ).exclude(
        id=order.id
    ).exists()

    if previous_orders and not previous_discount_used:
        order.returning_discount_used = True

    order.save()

    cart_items = CartItem.objects.filter(
        user=request.user
    )

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

        orderproduct.variations.set(
            item.variations.all()
        )

        orderproduct.save()

        product = item.product
        product.stock -= item.quantity
        product.save()

    coupon_id = request.session.get("coupon_id")

    if coupon_id and request.user.is_authenticated:
        try:
            coupon = Coupon.objects.get(
                id=coupon_id
            )

            CouponUsage.objects.get_or_create(
                user=request.user,
                coupon=coupon,
                defaults={
                    "order_id": order.order_number
                }
            )

            request.session.pop(
                "coupon_id",
                None
            )

        except Coupon.DoesNotExist:
            pass

    CartItem.objects.filter(
        user=request.user
    ).delete()

    data = {
        "order_number": order.order_number,
        "transID": payment.payment_id,
    }

    return JsonResponse(data)


def order_complete(request):
    order_number = request.GET.get(
        "order_number"
    )

    transID = request.GET.get(
        "payment_id"
    )

    try:
        order = Order.objects.get(
            order_number=order_number,
            is_ordered=True
        )

        ordered_products = OrderProduct.objects.filter(
            order_id=order.id
        )

        subtotal = sum(
            item.product_price * item.quantity
            for item in ordered_products
        )

        payment = Payment.objects.get(
            payment_id=transID
        )

        send_invoice_email(
            order,
            payment,
            ordered_products
        )

        context = {
            "order": order,
            "ordered_products": ordered_products,
            "order_number": order.order_number,
            "transID": payment.payment_id,
            "payment": payment,
            "subtotal": subtotal,
            "shipping": order.shipping_charge,
            "discount": order.discount_amount,
            "coupon_code": order.coupon_code,
            "grand_total": order.order_total,
        }

        return render(
            request,
            "orders/order_complete.html",
            context
        )

    except (
        Order.DoesNotExist,
        Payment.DoesNotExist
    ):
        return redirect("home")


@login_required
def order_status(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "orders/order_status.html",
        {
            "orders": orders
        }
    )