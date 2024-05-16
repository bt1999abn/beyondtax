from django.db import models
from django.utils.safestring import mark_safe

from accounts.models import WorkOrder
from shared import abstract_models


class Payment(abstract_models.BaseModel):
    STATUS_PENDING,STATUS_PARTIALLY_PAID, STATUS_PAID, STATUS_FAILED = 0, 1, 2, 3
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PARTIALLY_PAID, "Partially Paid"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    )

    payment_order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_signature = models.CharField(max_length=150, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.CharField(max_length=50, null=True, blank=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    attempts = models.PositiveIntegerField(default=0)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="work_order_payments")
    screen_shot = models.ImageField(upload_to='payment_ss_upload_path/', null=True, blank=False)

    def screen_shot_tag(self):
        return mark_safe(
            f'<img src="{self.screen_shot.url if self.screen_shot else ""}" width="150" height="150" />'
        )

    screen_shot_tag.short_description = 'Image'

    def __str__(self):
        return f"Payment {self.payment_id} for WorkOrder {self.work_order.id}"