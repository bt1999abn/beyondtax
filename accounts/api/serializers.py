from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.core.validators import RegexValidator
from django_filters import rest_framework as filters
from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import User, UpcomingDueDates, BusinessContactPersonDetails, OtpRecord

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email_or_mobile = serializers.CharField(required=False)
    password = serializers.CharField(max_length=128, required=True)
    token = serializers.CharField(required=False)
    user = serializers.SerializerMethodField()

    def validate(self, attrs):
        email_or_mobile = attrs.get('email_or_mobile')
        password = attrs.get('password')
        token = attrs.get('token')

        if token:
            user = authenticate(request=self.context.get('request'), token=token)
            if not user:
                raise serializers.ValidationError("Invalid or expired token")
        else:
            if not email_or_mobile or not password:
                raise serializers.ValidationError("Email or mobile and password are required for login.")
            try:
                if '@' in email_or_mobile:
                    user = User.objects.get(email=email_or_mobile)
                else:
                    user = User.objects.get(mobile_number=email_or_mobile)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist.")
            user = authenticate(username=email_or_mobile, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credetials.")
        attrs['user'] = user
        return attrs

    def get_user(self, obj):
        user = obj.get('user')
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'client_type': user.client_type,
            'contact_person': user.contact_person,
            'business_name': user.business_name,
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        }


class AuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class RegistrationSerializer(serializers.Serializer):
    mobile_regex = RegexValidator(
        regex=r'^[1-9][0-9]{9}$',
        message="Please enter a valid mobile number format."
    )
    client_type = serializers.ChoiceField(choices=User.CLIENT_TYPE_CHOICES, required=True)
    mobile_number = serializers.CharField(validators=[mobile_regex], max_length=10, min_length=10, required=False)
    full_name = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(format='%d-%m-%Y', input_formats=['%d-%m-%Y'], required=False)
    password = serializers.CharField(max_length=128, required=True)
    state = serializers.ChoiceField(choices=User.STATES_CHOICES, required=False)
    email = serializers.EmailField(required=False, allow_blank=False)

    business_name = serializers.CharField(required=False)
    business_contact_person = serializers.CharField(required=False)
    business_mobile_number = serializers.CharField(validators=[mobile_regex], max_length=10, min_length=10,
                                                   required=False)
    business_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        client_type = attrs.get('client_type')
        mobile_number = attrs.get('mobile_number')
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already used.")
        if User.objects.filter(mobile_number=mobile_number).exists():
            raise serializers.ValidationError("This mobile number already exists.")
        if client_type == User.Individual:
            if not attrs.get('full_name'):
                raise serializers.ValidationError("Full name is required for individual clients.")
            if User.objects.filter(email=attrs.get('email')).exists():
                raise serializers.ValidationError("This email is already used.")
        else:
            if not attrs.get('business_name'):
                raise serializers.ValidationError("Business name is required for non-individual clients.")
            if not attrs.get('business_contact_person'):
                raise serializers.ValidationError("Business contact person is required for non-individual clients.")
            if not attrs.get('business_mobile_number'):
                raise serializers.ValidationError("Business mobile number is required for non-individual clients.")
            if not attrs.get('business_email'):
                raise serializers.ValidationError("Business email is required for non-individual clients.")
            if User.objects.filter(business_email=attrs.get('business_email')).exists():
                raise serializers.ValidationError("This business email is already used.")

        return attrs

    def create(self, validated_data):
        client_type = validated_data.get('client_type')
        user = User(
            mobile_number=validated_data['mobile_number'],
            email=validated_data.get('email', ''),
            client_type=client_type,
            is_active=False,
        )
        if client_type == User.Individual:
            full_name = validated_data['full_name']
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        else:
            user.business_name = validated_data['business_name']
            user.business_contact_person = validated_data['business_contact_person']
            user.business_mobile_number = validated_data['business_mobile_number']
            user.business_email = validated_data['business_email']
            user.is_active = False
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserProfileSerializer(serializers.Serializer):
    mobile_regex = RegexValidator(
        regex=r'^[1-9][0-9]{9}$',
        message="Please enter a valid mobile number format."
    )

    mobile_number = serializers.CharField(validators=[mobile_regex], max_length=10, min_length=10)
    first_name = serializers.CharField(max_length=255, required=False)
    last_name = serializers.CharField(max_length=255, required=False)
    date_of_birth = serializers.DateField(format='%d-%m-%Y', input_formats=['%d-%m-%Y'], required=False)
    state = serializers.ChoiceField(choices=User.STATES_CHOICES, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, write_only=True)
    confirm_password = serializers.CharField(required=False, write_only=True)
    client_type = serializers.ChoiceField(choices=User.CLIENT_TYPE_CHOICES, required=False)
    industry_type = serializers.ChoiceField(choices=User.INDUSTRY_TYPE_CHOICES, required=False)
    nature_of_business = serializers.ChoiceField(choices=User.NATURE_OF_BUSINESS_CHOICES, required=False)
    contact_person = serializers.CharField(max_length=255, required=False)
    job_title = serializers.CharField(max_length=255, required=False)
    contact_person_phone_number = serializers.CharField(validators=[mobile_regex], max_length=10, required=False)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    business_name = serializers.CharField(max_length=255, required=False)
    date_of_formation = serializers.DateField(format='%d-%m-%Y', input_formats=['%d-%m-%Y'], required=False)
    business_mobile_number = serializers.CharField(validators=[mobile_regex], max_length=10, required=False)
    business_email = serializers.EmailField(required=False, allow_blank=True)
    number_of_employees = serializers.ChoiceField(choices=User.NUMBER_OF_EMPLOYEES_CHOICES, required=False)
    annual_revenue = serializers.DecimalField(max_digits=30, decimal_places=2, required=False, allow_null=True)

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")
        client_type = data.get('client_type', self.instance.client_type if self.instance else None)
        if client_type and client_type != User.Individual:
            required_business_fields = [
                'business_name', 'industry_type', 'date_of_formation',
                'business_mobile_number', 'business_email',
                'number_of_employees', 'annual_revenue'
            ]
            for field in required_business_fields:
                if not data.get(field):
                    raise serializers.ValidationError(
                        {field: f"{field.replace('_', ' ').capitalize()} is required for non-individual clients."})
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['profile_title'] = instance.get_profile_title()
        return representation

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.state = validated_data.get('state', instance.state)
        instance.email = validated_data.get('email', instance.email)
        instance.client_type = validated_data.get('client_type', instance.client_type)
        instance.industry_type = validated_data.get('industry_type', instance.industry_type)
        instance.nature_of_business = validated_data.get('nature_of_business', instance.nature_of_business)
        instance.contact_person = validated_data.get('contact_person', instance.contact_person)
        instance.job_title = validated_data.get('job_title', instance.job_title)
        instance.contact_person_phone_number = validated_data.get('contact_person_phone_number',
                                                                  instance.contact_person_phone_number)
        instance.contact_email = validated_data.get('contact_email', instance.contact_email)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)

        if instance.client_type != User.Individual:
            instance.business_name = validated_data.get('business_name', instance.business_name)
            instance.business_type = validated_data.get('industry_type', instance.industry_type)
            instance.date_of_formation = validated_data.get('date_of_formation', instance.date_of_formation)
            instance.business_mobile_number = validated_data.get('business_mobile_number',
                                                                 instance.business_mobile_number)
            instance.business_email = validated_data.get('business_email', instance.business_email)
            instance.number_of_employees = validated_data.get('number_of_employees', instance.number_of_employees)
            instance.annual_revenue = validated_data.get('annual_revenue', instance.annual_revenue)

        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user= self.context['request'].user
        old_password = attrs.get('old_password')
        if not user.check_password(old_password):
            raise serializers.ValidationError("Old Password is not correct")
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        if new_password != confirm_new_password:
            raise serializers.ValidationError({"confirm_new_password": "New passwords must match."})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class UserBasicDetailsSerializer(serializers.Serializer):
    full_name = serializers.SerializerMethodField()
    mobile_number = serializers.CharField(max_length=10)
    date_of_birth = serializers.DateField()
    email = serializers.EmailField()
    profile_picture = serializers.ImageField()
    profile_title = serializers.SerializerMethodField()
    client_type = serializers.ChoiceField(choices=User.CLIENT_TYPE_CHOICES)
    business_name = serializers.CharField()
    date_of_formation = serializers.DateField()
    business_mobile_number = serializers.CharField()
    business_email = serializers.EmailField()

    def get_full_name(self, obj):
        first_name = obj.first_name or ""
        last_name = obj.last_name or ""
        return f"{first_name} {last_name}".strip()

    def get_profile_title(self, obj):
        return obj.profile_title()


class UpcomingDueDateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UpcomingDueDates
        fields = ['date', 'compliance_activity', 'service_type', 'penalty_fine_interest']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.date:
            ret['date'] = instance.date.strftime('%d-%m-%Y')
        return ret


class UpcomingDueDatesFilter(filters.FilterSet):
    service_type = filters.NumberFilter(field_name='service_type')

    class Meta:
        model = UpcomingDueDates
        fields = ['service_type']


class BusinessContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessContactPersonDetails
        fields = '__all__'


class UserBusinessContactPersonsSerializer(serializers.ModelSerializer):
    contact_persons = BusinessContactPersonSerializer(many=True)

    class Meta:
        model = User
        fields = ['contact_persons']


class PasswordResetSerializer(serializers.Serializer):
    otp_id = serializers.IntegerField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        otp_id = attrs.get('otp_id')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            otp_record = OtpRecord.objects.get(id=otp_id)
            user = User.objects.get(email=otp_record.email)
            if check_password(password, user.password):
                raise serializers.ValidationError("New password cannot be the same as the old password.")
        except OtpRecord.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP ID.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        return attrs
