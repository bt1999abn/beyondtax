from django.contrib import admin
from payments.models import Payment
from workOrder.models import WorkOrderDocument, WorkOrderDownloadDocument, WorkOrder


# Register your models here.
class WorkOrderDocumentsInline(admin.TabularInline):
    model = WorkOrderDocument
    extra = 1


class WorkOrderDownloadDocumentInLine(admin.TabularInline):
    model = WorkOrderDownloadDocument
    extra = 1


class WorkOrderPaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


class WorkOrderAdmin(admin.ModelAdmin):
    inlines = [WorkOrderDocumentsInline, WorkOrderDownloadDocumentInLine, WorkOrderPaymentInline, ]
    list_display = ('service_name', 'amount_paid', 'status', 'user')
    search_fields = ('service_name', 'user__username')


admin.site.register(WorkOrder, WorkOrderAdmin)
