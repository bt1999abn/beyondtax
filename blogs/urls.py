from django.urls import path

from blogs.views import GetBlogPostApi, BlogPostDetailApi

urlpatterns = [
    # ... your other URL patterns
    path('getblogpost/', GetBlogPostApi.as_view(), name='blogpost-list'),
    path('blogpost-detail/<int:pk>/', BlogPostDetailApi.as_view(), name='blogpost-detail'),
]