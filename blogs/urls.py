from django.urls import path

from blogs.views import GetBlogPostApi, BlogPostDetailApi

urlpatterns = [

    path('getblogpost/', GetBlogPostApi.as_view(), name='blogpost-list'),
    path('blogpost-detail/<str:pk>/', BlogPostDetailApi.as_view(), name='blogpost-detail'),
]