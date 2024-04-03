from rest_framework import serializers
from django.contrib.auth import authenticate

from accounts.models import User


class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()

    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')

        if not mobile_number:
            raise serializers.ValidationError("Please give both email and password.")

        user = User.objects.filter(mobile_number=mobile_number).first()
        if not user:
            raise serializers.ValidationError('Mobile Number does not exist.')

        attrs['user'] = user
        return attrs
