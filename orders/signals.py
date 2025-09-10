# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .utils import credit_points_for_order

@receiver(post_save, sender=Order)
def handle_order_completed(sender, instance: Order, **kwargs):
    if instance.status == Order.Status.COMPLETED and not instance.points_awarded:
        credit_points_for_order(instance)
        instance.points_awarded = True
        instance.save(update_fields=["points_awarded"])