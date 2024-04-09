from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers, request
from django.contrib.auth.models import User  # Use get_user_model() if you have a custom user model
from accounts.models import User


class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')
        if not mobile_number:
            raise serializers.ValidationError("Mobile Number is required field.")
        password = attrs.get('password')

        if not password:
            raise serializers.ValidationError("Please give both email and password.")
        try:
            User.objects.get(mobile_number=mobile_number)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        user = authenticate(username=mobile_number, password=password)
        if user:
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('wrong credentials.')


class RegistrationSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()
    full_name = serializers.CharField()
    date_of_birth = serializers.DateField()
    state = serializers.ChoiceField(choices=User.STATES_CHOICES)
    email = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')
        if not mobile_number:
            raise serializers.ValidationError("Mobile Number is required field.")

        full_name = attrs.get('full_name')
        if not full_name:
            raise serializers.ValidationError("NAME is required field.")

        date_of_birth = attrs.get('date_of_birth')
        if not date_of_birth:
            raise serializers.ValidationError("Date of Birth is required field.")

        state = attrs.get('state')
        if not state:
            raise serializers.ValidationError("Please select the state.")
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already used.")
        if User.objects.filter(mobile_number=mobile_number).exists():
            raise serializers.ValidationError("This mobile number already exists.")
        name_parts = full_name.split(' ', 1)
        attrs['first_name'] = name_parts[0]
        attrs['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        return attrs

    def create(self, validated_data):
        user = User(mobile_number=validated_data['mobile_number'],
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'],
                    date_of_birth=validated_data['date_of_birth'],
                    state=validated_data['state'],
                    email=validated_data.get('email_id', ''),
                    is_active=False
                    )
        user.save()
        return user



