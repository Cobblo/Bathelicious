import os
from decimal import Decimal, ROUND_DOWN
from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from accounts.models import PointsLedger, PointsWallet

# ---------------------------------------------------------------------
# WeasyPrint / GTK setup (Windows)
# ---------------------------------------------------------------------
# Use a raw string or double backslashes for Windows paths
os.environ["PATH"] = r"C:\Program Files\GTK2-Runtime Win64\bin;" + os.environ.get("PATH", "")

from weasyprint import HTML

# ---------------------------------------------------------------------
# Shipping charge helper
# ---------------------------------------------------------------------
def calculate_shipping_charge(state):
    normalized = state.strip().lower()
    print(f"DEBUG State Input: '{state}' | Normalized: '{normalized}'")
    if normalized == "tamil nadu":
        return 80
    return 120


# ---------------------------------------------------------------------
# Invoice PDF generation
# ---------------------------------------------------------------------
def generate_invoice_pdf(order, payment, order_products):
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "new_logo1.png")
    assert os.path.exists(logo_path), f"Logo file not found at: {logo_path}"
    logo_url = "file:///" + logo_path.replace("\\", "/")

    processed_items = []
    subtotal = 0
    total_tax = 0

    for item in order_products:
        item_total = item.product_price * item.quantity
        # 12% GST on full line
        item_tax = (item.product_price * 0.12) * item.quantity
        subtotal += item_total
        total_tax += item_tax

        processed_items.append(
            {
                "product": item.product,
                "price": item.product_price,
                "quantity": item.quantity,
                "variations": item.variations.all(),
                "line_total": item_total,
                "tax": item_tax,
            }
        )

    shipping_charge = float(order.shipping_charge or 0)
    grand_total = subtotal + total_tax + shipping_charge

    html_string = render_to_string(
        "invoice/invoice.html",
        {
            "order": order,
            "payment": payment,
            "order_products": processed_items,
            "logo_url": logo_url,
            "subtotal": subtotal,
            "tax": total_tax,
            "shipping": shipping_charge,
            "grand_total": grand_total,
        },
    )

    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file


# ---------------------------------------------------------------------
# Invoice email sending (customer + admin copy)
# ---------------------------------------------------------------------
ADMIN_INVOICE_EMAIL = "ecopurenaturalsind@gmail.com"


def send_invoice_email(order, payment, order_products):
    """
    Sends invoice PDF:
      - To the customer (order.email)
      - BCC copy to ADMIN_INVOICE_EMAIL
    """
    subject = "Your Order Invoice - Bathelicious"
    to_email = order.email
    message = "Thank you for your order. Please find your invoice attached."

    email = EmailMessage(
        subject,
        message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[to_email],
        bcc=[ADMIN_INVOICE_EMAIL],   # 👈 admin gets every invoice copy
    )
    email.content_subtype = "html"

    # Generate PDF
    pdf_file = generate_invoice_pdf(order, payment, order_products)
    email.attach(
        f"Invoice_{order.order_number}.pdf",
        pdf_file.read(),
        "application/pdf",
    )
    email.send()


# ---------------------------------------------------------------------
# Points / loyalty
# ---------------------------------------------------------------------
EARN_RATE = Decimal("0.05")  # 5%


def credit_points_for_order(order):
    user = order.user
    eligible_amount = Decimal(order.get_eligible_amount())  # implement this on your model
    if eligible_amount <= 0:
        return

    credit = (eligible_amount * EARN_RATE).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )

    wallet = user.points_wallet
    new_balance = wallet.balance + credit

    # Ledger
    PointsLedger.objects.create(
        user=user,
        entry_type=PointsLedger.EARN,
        amount=credit,  # positive
        balance_after=new_balance,
        meta={"order_id": order.id, "note": "Points for purchase"},
    )

    # Wallet
    wallet.balance = new_balance
    wallet.save(update_fields=["balance"])
