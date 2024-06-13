from django.db.models import Sum
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.rest.pagination import CustomPagination
from workOrder import serializers
from workOrder.models import WorkOrderDownloadDocument, WorkOrder, WorkorderPayment
from workOrder.serializers import WorkOrderDocumentsUploadSerializer, WorkOrderDownloadDocumentListSerializer, \
    WorkOrderDownloadDocumentSerializer, WorkOrderSerializer, WorkorderPaymentSerializer


class WorkOrderApiView(APIView):

    permission_classes = (IsAuthenticated,)


class WorkOrderApi(CreateAPIView):
    serializer_class = WorkOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetWorkOrderApi(ListAPIView):
    serializer_class = WorkOrderSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return WorkOrder.objects.filter(user=user).order_by('-updated_at')


class WorkOrderDocumentUploadAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        try:
            work_order_id = request.data['work_order_id']
            work_order = WorkOrder.objects.get(id=work_order_id)
        except (KeyError, WorkOrder.DoesNotExist):
            return Response({"error": "Work order with the provided ID does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)
        documents = []
        for key, file in request.FILES.items():
            if key.startswith('documents['):
                index = key.split('[')[1].split(']')[0]
                document_name_key = f'documents[{index}].document_name'
                if document_name_key in request.data:
                    documents.append({
                        'document_name': request.data[document_name_key],
                        'document_file': file
                    })

        data = {
            'work_order_id': work_order_id,
            'documents': documents
        }

        serializer = WorkOrderDocumentsUploadSerializer(data=data, context={'work_order': work_order,
                                                                            'uploaded_by_beyondtax': False})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Documents uploaded successfully"}, status=status.HTTP_201_CREATED)


class WorkOrderDocumentUploadByBeyondtaxAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        try:
            work_order_id = request.data['work_order_id']
            work_order = WorkOrder.objects.get(id=work_order_id)
        except (KeyError, WorkOrder.DoesNotExist):
            return Response({"error": "Work order with the provided ID does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        documents = []
        for key, file in request.FILES.items():
            if key.startswith('documents['):
                index = key.split('[')[1].split(']')[0]
                document_name_key = f'documents[{index}].document_name'
                if document_name_key in request.data:
                    documents.append({
                        'document_name': request.data[document_name_key],
                        'document_file': file
                    })
        data = {
            'work_order_id': work_order_id,
            'documents': documents
        }
        serializer = WorkOrderDocumentsUploadSerializer(data=data, context={'work_order': work_order,
                                                                            'uploaded_by_beyondtax': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Documents uploaded successfully"}, status=status.HTTP_201_CREATED)


class WorkOrderDocumentApi(ListAPIView):
    serializer_class = WorkOrderDownloadDocumentSerializer
    permission_classes = (IsAuthenticated,)


class WorkOrderStatusSummaryApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,*args,**kwargs):
        user = request.user
        user_workorders = WorkOrder.objects.filter(user=user)
        inprocess_count = user_workorders.filter(status=1).count()
        download_count = user_workorders.filter(status=2).count()
        total_amount_paid = user_workorders.aggregate(Sum('amount_paid'))
        data = {
            "inprocess_count": inprocess_count,
            "download_count": download_count,
            "total_amount_paid": total_amount_paid if total_amount_paid else 0
        }
        return Response(data, status=status.HTTP_200_OK)


class WorkOrderDownloadDocumentApi(generics.RetrieveAPIView):
    serializer_class = WorkOrderDownloadDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self,*args,**kwargs):
        work_order_id = self.kwargs.get('work_order_id')
        if not work_order_id:
            raise ValueError("WorkOrder ID is required.")
        try:
            document = WorkOrderDownloadDocument.objects.get(work_order_id=work_order_id)
            return document
        except WorkOrderDownloadDocument.DoesNotExist:
            raise serializers.ValidationError(f"No document found for WorkOrder ID {work_order_id}.")


class WorkOrderDownloadDocumentListApi(generics.ListAPIView):
    serializer_class = WorkOrderDownloadDocumentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return WorkOrderDownloadDocument.objects.filter(work_order__user=user, work_order__status=5)


class WorkorderPaymentRetriveApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, work_order_id):
        try:
            work_order = WorkOrder.objects.get(id=work_order_id)
        except WorkOrder.DoesNotExist:
            return Response({"error": f"No WorkOrder found with ID {work_order_id}"}, status=status.HTTP_404_NOT_FOUND)
        payments = WorkorderPayment.objects.filter(work_order=work_order)
        if not payments.exists():
            return Response({"error": f"No payments found for WorkOrder ID {work_order_id}"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = WorkorderPaymentSerializer(payments, many=True)

        return Response(serializer.data)

