from django.urls import path

from . import views
from .views import WorkOrderDocumentUploadAPI, WorkOrderDocumentUploadByBeyondtaxAPI, WorkOrderStatusSummaryApi, \
    WorkorderPaymentRetriveApi

urlpatterns =[

    path('create-work-order/', views.WorkOrderApi.as_view()),
    path('list-work-order/', views.GetWorkOrderApi.as_view()),
    path('upload-documents/', WorkOrderDocumentUploadAPI.as_view(), name='upload-work-order-documents'),
    path('upload-documents-beyondtax/', WorkOrderDocumentUploadByBeyondtaxAPI.as_view(), name='upload-work-order-documents-by-beyondtax'),
    path('workorder-status-summary/', WorkOrderStatusSummaryApi.as_view(), name='workorder-status-summary'),
    path('workorder-download-document/<str:work_order_id>/', views.WorkOrderDownloadDocumentApi.as_view(),
         name='workorder-download-document'),
    path('workorder-download-document-list/', views.WorkOrderDownloadDocumentListApi.as_view(),
         name='workorder-download-document-list'),
    path('workorder-payment/<str:work_order_id>/', WorkorderPaymentRetriveApi.as_view(), name='workorder-payment'),


]