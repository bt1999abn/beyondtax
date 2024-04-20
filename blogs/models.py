from ckeditor.fields import RichTextField
from django.db import models

from shared import abstract_models


class BlogPost(abstract_models.BaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(default='Default description')
    content = RichTextField()
    category = models.CharField(max_length=100, blank=True, null=True)