from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView , RetrieveAPIView
from blogs.serializers import BlogPostSerializer, BlogPostDetailSerializer
from accounts.models import BlogPost


class GetBlogPostApi(ListAPIView):
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.all()
        blog_id = self.request.query_params.get('id', None)

        if blog_id is not None:
            queryset = queryset.filter(id=blog_id)
            if not queryset.exists():
                raise NotFound(detail="blogs not found")

        return queryset


class BlogPostDetailApi(RetrieveAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostDetailSerializer

