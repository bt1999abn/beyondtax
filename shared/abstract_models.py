from django.db import models


# BaseModel to create the models
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name if hasattr(self, 'name') else str(self.id)


class CharField(models.CharField):
    def clean(self, value, model_instance):
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.
        """
        value = super().clean(value, model_instance)
        return value.lower()


class TextField(models.TextField):
    def clean(self, value, model_instance):
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.
        """
        value = super().clean(value, model_instance)
        return value.lower()
