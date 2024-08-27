import base64

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, RetrieveAPIView
from blogs.models import BlogPost
from blogs.serializers import BlogPostSerializer, BlogPostDetailSerializer
from shared.libs.hashing import AlphaId
from shared.rest.pagination import CustomPagination


class GetBlogPostApi(ListAPIView):
    serializer_class = BlogPostSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = BlogPost.objects.all()
        encoded_blog_id = self.request.query_params.get('id', None)
        if encoded_blog_id is not None:
            try:
                blog_id = AlphaId.decode(encoded_blog_id)
                queryset = queryset.filter(id=blog_id)
                if not queryset.exists():
                    raise NotFound(detail="Blog posts not found")
            except ValueError:
                raise NotFound(detail="Invalid blog ID")
        return queryset


class BlogPostDetailApi(RetrieveAPIView):
    serializer_class = BlogPostDetailSerializer

    def get_object(self):
        encoded_pk = self.kwargs.get('pk')

        try:
            decoded_pk = AlphaId.decode(encoded_pk)
        except ValueError:
            raise NotFound("Invalid encoded ID.")

        blog_post = get_object_or_404(BlogPost, pk=decoded_pk)
        return blog_post
