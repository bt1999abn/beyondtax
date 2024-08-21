from django.db.models import Sum
from rest_framework import serializers
from accounts.models import ServicePages
from shared.libs.hashing import AlphaId
from shared.rest.serializers import BaseModelSerializer, BaseSerializer
from workOrder.models import WorkOrderDocument, WorkOrder, WorkOrderDownloadDocument, WorkorderPayment


class WorkOrderSerializer(BaseModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')
    service_id = serializers.CharField(write_only=True)
    service_name = serializers.SerializerMethodField()
    required_documents_list = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ('user', 'service', 'service_name')

    def get_required_documents_list(self, obj):
        if obj.service:
            return obj.service.get_required_documents_list()
        return []

    def get_service_name(self, obj):
        return obj.service.service_title if obj.service else None

    def validate_service_id(self, value):
        try:
            decoded_service_id = AlphaId.decode(value)
            service = ServicePages.objects.get(id=decoded_service_id)
            self.context['service'] = service
        except ServicePages.DoesNotExist:
            raise serializers.ValidationError(f"Service with ID {decoded_service_id} does not exist.")
        except ValueError:
            raise serializers.ValidationError("Invalid service ID format.")
        return decoded_service_id

    def create(self, validated_data):
        validated_data['service'] = self.context.get('service')
        validated_data['user'] = self.context['request'].user
        return WorkOrder.objects.create(**validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('first_instance', True):
            user_workorders = WorkOrder.objects.filter(user=instance.user)
            summary = {
                "inprocess_count": user_workorders.filter(status=3).count(),
                "download_count": user_workorders.filter(status=5).count(),
                "total_amount_paid": user_workorders.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
            }
            representation['summary'] = summary
            self.context['first_instance'] = False
        return representation


class DocumentSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(max_length=255)
    document_file = serializers.FileField()

    class Meta:
        model = WorkOrderDocument
        fields = ['document_name', 'document_file']


class WorkOrderDocumentsUploadSerializer(BaseModelSerializer):
    work_order_id = serializers.CharField(write_only=True)
    documents = DocumentSerializer(many=True, write_only=True)

    class Meta:
        model = WorkOrderDocument
        fields = ['work_order_id', 'documents']

    def validate_work_order_id(self, value):
        try:
            work_order = WorkOrder.objects.get(id=value)
        except WorkOrder.DoesNotExist:
            raise serializers.ValidationError(f"Work order with ID {value} does not exist.")
        self.context['work_order'] = work_order
        return value

    def validate_documents(self, value):
        work_order = self.context.get('work_order')
        if not work_order:
            raise serializers.ValidationError("Work order must be provided to validate document names.")
        required_docs_list = work_order.service.get_required_documents_list()
        for document in value:
            if document['document_name'] not in required_docs_list:
                raise serializers.ValidationError(
                    f"Document name '{document['document_name']}' is not in the required documents list: {required_docs_list}")
        return value

    def create(self, validated_data):
        work_order = self.context['work_order']
        documents = validated_data.pop('documents')
        uploaded_by_beyondtax = self.context['uploaded_by_beyondtax']
        for document_data in documents:
            WorkOrderDocument.objects.create(work_order=work_order, uploaded_by_beyondtax=uploaded_by_beyondtax,
                                             **document_data)
        return work_order


class WorkOrderDownloadDocumentSerializer(BaseModelSerializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderDownloadDocument
        fields = ['id', 'work_order', 'download_document', 'description', 'document_url']

    def get_document_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.download_document.url)
        return None


class WorkOrderDownloadDocumentListSerializer(BaseModelSerializer):
    document_url = serializers.SerializerMethodField()
    wo_dept = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderDownloadDocument
        fields = ['id', 'work_order', 'download_document', 'description', 'wo_dept',
                  'document_url']

    def get_document_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.download_document.url)
        return None

    def get_wo_dept(self, obj):
        return obj.work_order.wo_dept if obj.work_order else None


class WorkorderPaymentSerializer(BaseModelSerializer):
    class Meta:
        model = WorkorderPayment
        fields = ['work_order', 'bank_account', 'ifsc_code', 'recipient_name', 'qr_code_url',
                  'amount_due']