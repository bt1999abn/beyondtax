from django.urls import path
from . import views

urlpatterns = [

    path('service-pages/', views.ServicePagesApi.as_view(), name='service-pages'),
    path('services-list/',views.ListServicePagesApi.as_view(), name ='services-list')

]