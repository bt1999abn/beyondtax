from django.urls import path
from .views import IncomeTaxProfileApi, ListIncomeTaxReturnsView, ResidentialStatusQuestionsListView

urlpatterns = [
    path('create-incometax-profile/', IncomeTaxProfileApi.as_view(), name='create-incometax-profile'),
    path('update-incometax-profile/', IncomeTaxProfileApi.as_view(), name='update-incometax-profile'),
    path('retrive-incometax-profile/', IncomeTaxProfileApi.as_view(), name='retrive-incometax-profile'),
    path('income-tax-returns/', ListIncomeTaxReturnsView.as_view(), name='user-income-tax-returns'),
    path('residential-status-questions/', ResidentialStatusQuestionsListView.as_view(), name='residential-status-questions'),
]