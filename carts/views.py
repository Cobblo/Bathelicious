from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from store.models import Product, Variation, Coupon
from .models import Cart, CartItem
from .points import apply_redeem
from orders.models import Order
from orders.forms import OrderForm


# ---------- Helpers ----------
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def _shipping_amount(total):
    if total >= 1199:
        return Decimal("0.00")
    return Decimal("80.00")


def get_user_cart(user):
    """
    Placeholder helper for redeem points flow.
    """
    return None


def _get_cart_items(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user, is_active=True)

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        return CartItem.objects.filter(cart=cart, is_active=True)
    except Cart.DoesNotExist:
        return CartItem.objects.none()


# ---------- Cart ops ----------
def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except:
                pass

    # Logged-in user
    if current_user.is_authenticated:
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id_list = []

            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')

    # Guest user
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            ex_var_list = []
            id_list = []

            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
            except Cart.DoesNotExist:
                return redirect('cart')

        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


# ---------- Pages ----------
def cart(request, total=0, quantity=0, cart_items=None):
    discount = Decimal("0.00")
    coupon = None
    shipping = Decimal("0.00")
    original_total = Decimal("0.00")

    try:
        cart_items = _get_cart_items(request)

        for cart_item in cart_items:
            total += Decimal(str(cart_item.product.price)) * cart_item.quantity
            quantity += cart_item.quantity

        shipping = _shipping_amount(total) if total > 0 else Decimal("0.00")
        original_total = total + shipping

        coupon_id = request.session.get("coupon_id")
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, is_active=True)
                is_valid, message, discount = coupon.validate_coupon(
                    user=request.user,
                    cart_items=cart_items,
                    Order=Order
                )
                if not is_valid:
                    request.session.pop("coupon_id", None)
                    coupon = None
                    discount = Decimal("0.00")
                    messages.error(request, message)
            except Coupon.DoesNotExist:
                request.session.pop("coupon_id", None)
                coupon = None
                discount = Decimal("0.00")

        grand_total = total + shipping - discount

    except (ObjectDoesNotExist, Cart.DoesNotExist):
        shipping = Decimal("0.00")
        grand_total = Decimal("0.00")
        discount = Decimal("0.00")
        coupon = None
        original_total = Decimal("0.00")
        cart_items = []

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping': shipping,
        'discount': discount,
        'coupon': coupon,
        'original_total': original_total,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    discount = Decimal("0.00")
    coupon = None
    shipping = Decimal("0.00")
    original_total = Decimal("0.00")
    returning_customer_discount = Decimal("0.00")

    previous_paid_order = Order.objects.filter(
        user=request.user,
        is_ordered=True
    ).exists()

    already_used = Order.objects.filter(
        user=request.user,
        returning_discount_used=True
    ).exists()

    if previous_paid_order and not already_used:
        returning_customer_discount = Decimal("100.00")

    try:
        cart_items = _get_cart_items(request)

        for cart_item in cart_items:
            total += Decimal(str(cart_item.product.price)) * cart_item.quantity
            quantity += cart_item.quantity

        shipping = _shipping_amount(total) if total > 0 else Decimal("0.00")
        original_total = total + shipping

        coupon_id = request.session.get("coupon_id")
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, is_active=True)
                is_valid, message, discount = coupon.validate_coupon(
                    user=request.user,
                    cart_items=cart_items,
                    Order=Order
                )
                if not is_valid:
                    request.session.pop("coupon_id", None)
                    coupon = None
                    discount = Decimal("0.00")
                    messages.error(request, message)
            except Coupon.DoesNotExist:
                request.session.pop("coupon_id", None)
                coupon = None
                discount = Decimal("0.00")

        grand_total = (
            total +
            shipping -
            discount -
            returning_customer_discount
        )

    except (ObjectDoesNotExist, Cart.DoesNotExist):
        shipping = Decimal("0.00")
        grand_total = Decimal("0.00")
        discount = Decimal("0.00")
        coupon = None
        original_total = Decimal("0.00")
        returning_customer_discount = Decimal("0.00")
        cart_items = []

    form = OrderForm()

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping': shipping,
        'discount': discount,
        'returning_customer_discount': returning_customer_discount,
        'coupon': coupon,
        'original_total': original_total,
        'grand_total': grand_total,
        'form': form,
    }

    return render(request, 'store/checkout.html', context)


@login_required
def redeem_points(request):
    if request.method == "POST":
        try:
            requested = Decimal(request.POST.get("redeem_amount", "0"))
        except:
            requested = Decimal("0")

        cart = get_user_cart(request.user)
        actual = apply_redeem(request.user, cart, requested)

        if actual > 0:
            messages.success(request, f"₹{actual} redeemed from your points.")
        else:
            messages.warning(request, "Cannot redeem that amount.")

    return redirect("cart")


def apply_coupon(request):
    if request.method != "POST":
        return redirect("cart")

    coupon_code = request.POST.get("coupon_code", "").strip()

    if not coupon_code:
        request.session.pop("coupon_id", None)
        messages.error(request, "Please enter an offer code.")
        return redirect("cart")

    cart_items = _get_cart_items(request)

    if not cart_items.exists():
        request.session.pop("coupon_id", None)
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    try:
        coupon = Coupon.objects.get(code__iexact=coupon_code)
    except Coupon.DoesNotExist:
        request.session.pop("coupon_id", None)
        messages.error(request, "Invalid offer code.")
        return redirect("cart")

    if not coupon.is_active:
        request.session.pop("coupon_id", None)
        messages.error(request, "This coupon is inactive.")
        return redirect("cart")

    is_valid, message, discount = coupon.validate_coupon(
        user=request.user,
        cart_items=cart_items,
        Order=Order
    )

    if not is_valid:
        request.session.pop("coupon_id", None)
        messages.error(request, message)
        return redirect("cart")

    request.session["coupon_id"] = coupon.id
    messages.success(request, f"Offer code '{coupon.code}' applied successfully.")
    return redirect("cart")


def remove_coupon(request):
    request.session.pop("coupon_id", None)
    messages.success(request, "Coupon removed.")
    return redirect("cart")