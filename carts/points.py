# cart/points.py
from decimal import Decimal, ROUND_DOWN
from accounts.models import PointsLedger

REDEEM_CHUNK = Decimal("500.00")  # Only in 500s

def max_redeem_allowed(cart_item_count: int, wallet_balance: Decimal) -> Decimal:
    # 1 × 500 per product
    by_items = REDEEM_CHUNK * cart_item_count
    # Only full 500-chunks from balance
    chunks_by_balance = (wallet_balance // REDEEM_CHUNK) * REDEEM_CHUNK
    return min(by_items, chunks_by_balance)

def apply_redeem(user, cart, requested_amount: Decimal):
    """
    requested_amount is what the user attempts to redeem (e.g., 500, 1000, 1500).
    We clamp to valid chunks and per-product limit.
    Returns: actual_redeem (Decimal)
    """
    wallet = user.points_wallet
    item_count = cart.distinct_product_count()  # implement on your cart

    allowed = max_redeem_allowed(item_count, wallet.balance)
    if allowed <= 0:
        return Decimal("0.00")

    # Force to multiples of 500 and not above allowed
    chunks = (requested_amount // REDEEM_CHUNK)
    actual = min(allowed, chunks * REDEEM_CHUNK)

    if actual <= 0:
        return Decimal("0.00")

    # Deduct from wallet + ledger entry
    new_balance = wallet.balance - actual
    PointsLedger.objects.create(
        user=user,
        entry_type=PointsLedger.REDEEM,
        amount=Decimal("-1") * actual,    # negative
        balance_after=new_balance,
        meta={"note": "Checkout redeem"},
    )
    wallet.balance = new_balance
    wallet.save(update_fields=["balance"])

    # Attach to cart/session so totals reflect it
    cart.set_points_discount(actual)  # implement this; store on cart or session

    return actual