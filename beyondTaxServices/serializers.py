from rest_framework import serializers
from accounts.models import ServicePages


class ServicePagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePages
        fields = ('id', 'service_title', 'service_description', 'certificate_price', 'registration_title', 'what_is',
                  'step_by_step_title', 'step_by_step_description', 'faq_title', 'faq_description', 'faq', 'slug')


class ServicePagesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePages
        fields = ('id', 'service_title')
