from django.urls import path
from .views import IncomeTaxProfileApi, ListIncomeTaxReturnsView, ResidentialStatusQuestionsListView, \
    SendPanVerificationOtpApi, VerifyPanOtpApi, ImportIncomeTaxProfileDataApi

urlpatterns = [
    path('create-incometax-profile/', IncomeTaxProfileApi.as_view(), name='create-incometax-profile'),
    path('update-incometax-profile/', IncomeTaxProfileApi.as_view(), name='update-incometax-profile'),
    path('retrive-incometax-profile/', IncomeTaxProfileApi.as_view(), name='retrive-incometax-profile'),
    path('income-tax-returns/', ListIncomeTaxReturnsView.as_view(), name='user-income-tax-returns'),
    path('residential-status-questions/', ResidentialStatusQuestionsListView.as_view(), name='residential-status-questions'),
    path('send-pan-verification-otp/', SendPanVerificationOtpApi.as_view(), name='send_pan_verification_otp'),
    path('verify-pan-otp/', VerifyPanOtpApi.as_view(), name='verify_pan_otp'),
    path('import-tax-profile-data/', ImportIncomeTaxProfileDataApi.as_view(), name='import_tax_profile_data'),
]