from django.urls import path
from accounts.api import views as accounts_api_views
from knox.views import LogoutView, LogoutAllView
from .views import UpcomingDueDatesApi, BusinessContactPersonAPIView, \
    SendEmailOtpApi, VerifyEmailOtpApi, SendEmailApi, ResetPasswordApi

urlpatterns =[

    path('login/', accounts_api_views.LoginAPIView.as_view(), name='send_otp'),
    path('send_otp/', accounts_api_views.sendOtpApi.as_view(), name='send_otp'),
    path('registration/', accounts_api_views.RegistrationApiView.as_view(), name='registering_user'),
    path('get-profile/', accounts_api_views.ProfileApiView.as_view(), name='get-profile'),
    path('verify_otp/', accounts_api_views.VerifyOtpApiView.as_view(), name='verify_otp'),
    path('update-profile/', accounts_api_views.UpdateProfileApi.as_view(), name='update-profile'),
    path('logout/', LogoutView.as_view()),
    path('logout-all/', LogoutAllView.as_view()),
    path('change-password/',accounts_api_views.ChangePasswordAPI.as_view(), name='change-password-api'),
    path('user-basic-details/', accounts_api_views.UserBasicDetailsApi.as_view(), name='user-basic-details'),
    path('upcoming-due_dates/', UpcomingDueDatesApi.as_view(), name='upcoming-due_dates'),
    path('send-email-otp/',SendEmailOtpApi.as_view(), name='send-email-otp'),
    path('verify-email-otp/',VerifyEmailOtpApi.as_view(), name='verify-email-otp'),
    path('send-email/',SendEmailApi.as_view(), name='send-email'),
    path('create-business-contact-person/',BusinessContactPersonAPIView.as_view(), name='create-business-contact-person'),
    path('list-business-contact-person/',BusinessContactPersonAPIView.as_view(), name='list-business-contact-person'),
    path('update-business-contact-person/<int:pk>/',BusinessContactPersonAPIView.as_view(), name='list-business-contact-person'),
    path('reset-password/',ResetPasswordApi.as_view(), name='reset-password'),
]
