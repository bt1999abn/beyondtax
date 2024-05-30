from django.urls import path
from . import views

urlpatterns = [
    path('route/', views.sample_view, name='sample_view_one'),
]