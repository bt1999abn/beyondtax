from django.urls import path
from .views import IncomeTaxProfileApi, IncomeTaxBankDetailsView, ListIncomeTaxReturnsView

urlpatterns = [
    path('create-incometax-profile/', IncomeTaxProfileApi.as_view(), name='create-incometax-profile'),
    path('update-incometax-profile/', IncomeTaxProfileApi.as_view(), name='update-incometax-profile'),
    path('create-incometax-bank-details/', IncomeTaxBankDetailsView.as_view(), name='create-incometax-bank-details'),
    path('list-incometax-bank-details/', IncomeTaxBankDetailsView.as_view(), name='list-incometax-bank-details'),
    path('update-incometax-bank-details/<int:pk>/', IncomeTaxBankDetailsView.as_view(), name='update-incometax-bank-details'),
    path('delete-incometax-bank-details/<int:pk>/', IncomeTaxBankDetailsView.as_view(), name='delete-incometax-bank-details'),
    path('income-tax-returns/', ListIncomeTaxReturnsView.as_view(), name='user-income-tax-returns'),
]