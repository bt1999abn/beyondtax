from django.urls import path
from payments.views import PaymentListAPIView, PaymentCreateAPIView, PaymentVerifyAPIView

urlpatterns = [
    path('list-payment/', PaymentListAPIView.as_view(), name='list-payments'),
    path('create-payment/', PaymentCreateAPIView.as_view(), name='create-payment'),
    path('verify-payment/', PaymentVerifyAPIView.as_view(), name='payment-verify'),
]