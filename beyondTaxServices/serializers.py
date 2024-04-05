from rest_framework import serializers
from accounts.models import ServicePages


class ServicePagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePages
        fields = '__all__'