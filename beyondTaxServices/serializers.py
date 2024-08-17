from accounts.models import ServicePages
from shared.rest.serializers import BaseModelSerializer


class ServicePagesSerializer(BaseModelSerializer):
    class Meta:
        model = ServicePages
        fields = ('id', 'service_title', 'service_description', 'certificate_price', 'registration_title', 'what_is',
                  'step_by_step_title', 'step_by_step_description', 'faq_title', 'faq_description', 'faq', 'slug')


class ServicePagesListSerializer(BaseModelSerializer):
    class Meta:
        model = ServicePages
        fields = ('id', 'service_title')
