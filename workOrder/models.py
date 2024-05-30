from decimal import Decimal

from django.db import models

from accounts.models import ServicePages
from beyondTax import settings
from shared import abstract_models


class WorkOrder(abstract_models.BaseModel):
    Requested, Upload, Inprocess, Pay, Download= 1, 2, 3, 4, 5
    STATUS_CHOICES = (
        (Requested, "Requested"),
        (Upload, "Upload"),
        (Inprocess, "Inprocess"),
        (Pay, "Pay"),
        (Download, "Download"),

    )
    service_name = models.CharField(max_length=255, blank=False)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=Decimal('0.00'),  blank=False)
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=False, default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='work_orders')
    service = models.ForeignKey(ServicePages, related_name='work_order_files', null=True, on_delete=models.CASCADE)
    wo_dept = models.CharField(max_length=255, blank=True)
    requested_by = models.CharField(max_length=255, blank=True)
    client_id = models.IntegerField(blank=True, null=True)
    client_type = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    frequency = models.CharField(max_length=255, blank=True)
    schedule_date = models.DateField(blank=True, null=True)
    schedule_time = models.TimeField(blank=True, null=True)
    started_on = models.DateTimeField(blank=True, null=True)
    ended_on = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):

        if self.service:
            self.wo_dept = self.service.category
            self.service_name = self.service.service_title
            self.frequency = self.service.frequency
        if self.user:
            self.client_id = self.user.id
            self.requested_by = self.user.first_name
            self.client_type = self.user.client_type
        super(WorkOrder, self).save(*args, **kwargs)

    def __str__(self):
        return f"WorkOrder ID: {self.id} for {self.service_name}"


class WorkOrderDocument(abstract_models.BaseModel):
    work_order = models.ForeignKey(WorkOrder, related_name='work_order', on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255, blank=False, default='file name')
    document_file = models.FileField(upload_to='work_order_document_files/')
    uploaded_by_beyondtax = models.BooleanField(default=False)


class WorkOrderDownloadDocument(abstract_models.BaseModel):
    work_order = models.ForeignKey('WorkOrder', on_delete=models.CASCADE)
    download_document = models.FileField(upload_to='work_order_download_documents/')
    description = models.CharField(max_length=255, blank=True)


class WorkorderPayment(abstract_models.BaseModel):
    work_order = models.ForeignKey(WorkOrder, related_name='payments', on_delete=models.CASCADE)
    bank_account = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=11)
    recipient_name = models.CharField(max_length=255)
    qr_code_url = models.URLField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment for WorkOrder ID: {self.work_order.id}"