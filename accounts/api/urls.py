from django.urls import path

from accounts.api import views as accounts_api_views

urlpatterns = [
    path('login/', accounts_api_views.LoginAPIView.as_view(), name='send_otp'),
    path('send_otp/', accounts_api_views.sendOtpApi.as_view(), name='send_otp'),
]