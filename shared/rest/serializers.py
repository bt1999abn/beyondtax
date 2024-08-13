from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.relations import RelatedField

from shared.libs.hashing import AlphaId
from django.db import models
from rest_framework.fields import (  # NOQA # isort:skip
    BooleanField, CharField as RestCharField, ChoiceField, DateField, DateTimeField as RestDateTimeField, DecimalField,
    DictField, DurationField, EmailField, Field, FileField, FilePathField, FloatField,
    HiddenField, HStoreField, IPAddressField, ImageField, IntegerField, JSONField,
    ListField, ModelField, MultipleChoiceField, ReadOnlyField,
    RegexField, SerializerMethodField, SlugField, TimeField as RestTimeField, URLField, UUIDField,
)


class EncodeAlphaID:
    def get_id(self, instance):
        id_ = ""
        if type(instance) is dict:
            if "id" in instance:
                id_ = AlphaId.encode(instance["id"])
        else:
            id_ = AlphaId.encode(instance.id)
        return id_


class EncodeIdField(serializers.CharField):
    def to_representation(self, value):
        value = super().to_representation(value)
        value = AlphaId.encode(value)
        return value

    def to_internal_value(self, data):
        if type(data) is not str:
            raise serializers.ValidationError("The given id is invalid.")
        decoded_value = AlphaId.decode(data)
        if type(decoded_value) is not int or decoded_value < 0:
            raise serializers.ValidationError("The given id is invalid.")
        return super().to_internal_value(decoded_value)


class DecodeIdField(serializers.CharField):
    def to_internal_value(self, data):
        if type(data) is not str:
            raise serializers.ValidationError("The given id is invalid.")
        decoded_value = AlphaId.decode(data)
        if type(decoded_value) is not int or decoded_value < 0:
            raise serializers.ValidationError("The given id is invalid.")
        return super().to_internal_value(decoded_value)


class BasePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        value = super().to_representation(value)
        if self.use_pk_only_optimization():
            value = AlphaId.encode(value)
        return value

    def to_internal_value(self, data):
        if type(data) is not str:
            self.fail('incorrect_type', data_type=type(data).__name__)
        else:
            return super().to_internal_value(
                AlphaId.decode(data)
            )


class CharField(RestCharField):
    def to_representation(self, value):
        return super().to_representation(value).title()


class TimeField(RestTimeField):
    def __init__(self, format="%I:%M %p", input_formats=None, **kwargs):
        self.format = format
        if input_formats is not None:
            self.input_formats = input_formats
        super().__init__(**kwargs)


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=data)
        except (TypeError, ValueError):
            self.fail('invalid')


class StringPrimaryKeyRelatedField(RelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return True

    def to_internal_value(self, data):
        if type(data) is not str:
            self.fail('incorrect_type', data_type=type(data).__name__)
        data = AlphaId.decode(data)
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        queryset = self.get_queryset()
        try:
            if isinstance(data, bool):
                raise TypeError
            return queryset.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.pk)
        return AlphaId.encode(value.pk)


class BaseModelSerializer(EncodeAlphaID, serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    serializer_related_field = StringPrimaryKeyRelatedField
    serializer_field_mapping = {
        models.AutoField: IntegerField,
        models.BigIntegerField: IntegerField,
        models.BooleanField: BooleanField,
        models.CharField: CharField,
        models.CommaSeparatedIntegerField: CharField,
        models.DateField: DateField,
        models.DateTimeField: RestDateTimeField,
        models.DecimalField: DecimalField,
        models.DurationField: DurationField,
        models.EmailField: EmailField,
        models.Field: ModelField,
        models.FileField: FileField,
        models.FloatField: FloatField,
        models.ImageField: ImageField,
        models.IntegerField: IntegerField,
        models.NullBooleanField: BooleanField,
        models.PositiveIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        models.SlugField: SlugField,
        models.SmallIntegerField: IntegerField,
        models.TextField: CharField,
        models.TimeField: TimeField,
        models.URLField: URLField,
        models.UUIDField: UUIDField,
        models.GenericIPAddressField: IPAddressField,
        models.FilePathField: FilePathField,
    }


class EncodedIdModelSerializer(BaseModelSerializer):
    id = serializers.SerializerMethodField()


class BaseSerializer(EncodeAlphaID, serializers.Serializer):
    serializer_related_field = BasePrimaryKeyRelatedField
    id = serializers.SerializerMethodField()


class MultiSerializerClassViewSetMixin(object):
    """
    We can define multiple Serializer for a ViewSet using this Mixin.
    serializer_classes: takes a dict as input with actions defined as keys and the respective serializer to use as their values
    """
    serializer_classes = None

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action) if hasattr(self, 'action') else None
