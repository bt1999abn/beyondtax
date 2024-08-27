from blogs.models import BlogPost
from shared.rest.serializers import BaseModelSerializer


class BlogPostSerializer(BaseModelSerializer):
    class Meta:
        model = BlogPost
        exclude = ['content']


class BlogPostDetailSerializer(BaseModelSerializer):
    class Meta:
        model = BlogPost
        fields = '__all__'