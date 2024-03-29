from django.urls import path
from . import views
urlpatterns = [
    path('send_otp/', views.sendOtpApi.as_view(), name='send_otp'),
    path('verify_otp/', views.verifyOtpApi.as_view(), name='verify_otp'),
]