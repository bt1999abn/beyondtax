from django.urls import path
from accounts.api import views as accounts_api_views
from knox.views import LogoutView, LogoutAllView
from . import views
from .views import WorkOrderDocumentUploadAPI

urlpatterns =[

    path('login/', accounts_api_views.LoginAPIView.as_view(), name='send_otp'),
    path('send_otp/', accounts_api_views.sendOtpApi.as_view(), name='send_otp'),
    path('registration/', accounts_api_views.RegistrationApiView.as_view(), name='registering_user'),
    path('get-profile/', accounts_api_views.ProfileApiView.as_view(), name='get-profile'),
    path('verify_otp/', accounts_api_views.VerifyOtpApiView.as_view(), name='verify_otp'),
    path('update-profile/', accounts_api_views.UpdateProfileApi.as_view(), name='update-profile'),
    path('logout/', LogoutView.as_view()),
    path('logout-all/', LogoutAllView.as_view()),
    path('create-work-order/', views.WorkOrderApi.as_view()),
    path('list-work-order/', views.GetWorkOrderApi.as_view()),
    path('upload-documents/', WorkOrderDocumentUploadAPI.as_view(), name='upload-work-order-documents'),
    path('change-password/',accounts_api_views.ChangePasswordAPI.as_view(), name='change-password-api'),
    path('workorder-status-summary/', accounts_api_views.WorkOrderStatusSummaryApi.as_view(), name='workorder-status-summary'),
    path('user-basic-details/', accounts_api_views.UserBasicDetailsApi.as_view(), name='user-basic-details'),
    path('workorder-download-document/', views.WorkOrderDocumentListView.as_view(), name='workorder-download-document')
]
