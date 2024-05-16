from django.shortcuts import render
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        work_order_id = request.query_params.get('work_order_id')
        if work_order_id:
            payments = Payment.objects.filter(work_order__id=work_order_id)
        else:
            payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['status'] = Payment.STATUS_PENDING
            payment = serializer.save()
            workorder = payment.work_order
            new_payment_amount = payment.amount
            total_paid = sum(p.amount for p in Payment.objects.filter(work_order=workorder))
            new_total_paid = total_paid + new_payment_amount
            remaining_amount = workorder.service.certificate_price - new_total_paid
            workorder.amount_paid = new_total_paid
            workorder.save()
            response_data = serializer.data
            response_data['remaining_amount'] = max(remaining_amount, 0)
            response_data['payment_status'] = 'Pending'
            response_data['payment_id'] = payment.id
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        payment_id = request.data.get('payment_id')
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment:
            total_paid = sum(p.amount for p in Payment.objects.filter(work_order=payment.work_order)) + payment.amount
            service_amount = payment.work_order.service.certificate_price

            if total_paid >= service_amount:
                payment.status = Payment.STATUS_PAID
                Payment.objects.filter(work_order=payment.work_order).update(status=Payment.STATUS_PAID)
            else:
                payment.status = Payment.STATUS_PARTIALLY_PAID
            payment.save()
            response_data = {
                "message": "Payment verified successfully.",
                "status": "Paid" if payment.status == Payment.STATUS_PAID else "Partially Paid",
                "total_paid": total_paid,
                "remaining_amount": max(service_amount - total_paid, 0)
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)