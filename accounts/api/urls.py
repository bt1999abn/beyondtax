from django.urls import path
from accounts.api import views as accounts_api_views
from knox.views import LogoutView, LogoutAllView
from . import views
from .views import UpcomingDueDatesApi, SendOtpView, VerifyOtpView, SendEmailView

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
    path('send-email-otp/',SendOtpView.as_view(), name='send-email-otp'),
    path('verify-email-otp/',VerifyOtpView.as_view(), name='verify-email-otp'),
    path('send-email/',SendEmailView.as_view(), name='send-email'),
]
