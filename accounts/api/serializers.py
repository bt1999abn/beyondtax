import datetime
from datetime import date
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django_filters import rest_framework as filters
from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import User, UpcomingDueDates, BusinessContactPersonDetails, OtpRecord, ProfileInformation, \
    ProfileAddress, GovernmentID, ProfileBankAccounts
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxReturnYears, IncomeTaxReturn
from shared.libs.hashing import AlphaId
from shared.rest.serializers import BaseSerializer, BaseModelSerializer

User = get_user_model()


class LoginSerializer(BaseSerializer):
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
                raise serializers.ValidationError("Invalid credentials.")
        attrs['user'] = user
        return attrs

    def get_user(self, obj):
        user = obj.get('user')
        full_name = f"{user.first_name} {user.last_name or ''}".strip()
        try:
            income_tax_profile = user.income_tax_profile
            pan_no = income_tax_profile.pan_no.upper() if income_tax_profile else None
        except IncomeTaxProfile.DoesNotExist:
            pan_no = None
        current_date = date.today()
        try:
            current_year_record = IncomeTaxReturnYears.objects.get(
                start_date__lte=current_date, end_date__gte=current_date
            )
            current_income_tax_return = IncomeTaxReturn.objects.get(
                user=user, income_tax_return_year=current_year_record
            )
            current_income_tax_return_id = AlphaId.encode(current_income_tax_return.id)
            current_income_tax_return_year_name = current_income_tax_return.income_tax_return_year.name
        except ObjectDoesNotExist:
            current_income_tax_return_id = None
            current_income_tax_return_year_name = None

        return {
            'id': AlphaId.encode(user.id),
            'full_name': full_name,
            'email': user.email,
            'mobile_number': user.mobile_number,
            'date_of_birth': user.date_of_birth,
            'pan_no': pan_no,
            'client_type': user.client_type,
            'contact_person': user.contact_person,
            'business_name': user.business_name,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'current_income_tax_return_id': current_income_tax_return_id,
            'current_income_tax_return_year_name': current_income_tax_return_year_name,
        }


class AuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class RegistrationSerializer(BaseModelSerializer):
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

    class Meta:
        model = User
        fields = [
            'id', 'client_type', 'mobile_number', 'full_name', 'date_of_birth', 'password',
            'state', 'email', 'business_name', 'business_contact_person', 'business_mobile_number', 'business_email'
        ]

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
            if not attrs.get('business_mobile_number'):
                raise serializers.ValidationError("Business mobile number is required for non-individual clients.")

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
            user.business_mobile_number = validated_data['business_mobile_number']
            user.email = validated_data['email']
            user.is_active = False
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserProfileSerializer(BaseSerializer):
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


class ChangePasswordSerializer(BaseSerializer):
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


class UserBasicDetailsSerializer(BaseModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_title = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'mobile_number', 'date_of_birth', 'email',
            'profile_picture', 'profile_title', 'client_type',
            'business_name', 'date_of_formation', 'business_mobile_number', 'business_email'
        ]

    def get_full_name(self, obj):
        first_name = obj.first_name or ""
        last_name = obj.last_name or ""
        return f"{first_name} {last_name}".strip()

    def get_profile_title(self, obj):
        return obj.profile_title()


class UpcomingDueDateSerializer(BaseModelSerializer):
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = UpcomingDueDates
        fields = ['id','formatted_date', 'date', 'compliance_activity', 'service_type', 'penalty_fine_interest']

    def get_formatted_date(self, obj):
        return obj.date.strftime('%d-%m-%Y')


class UpcomingDueDatesFilter(filters.FilterSet):
    service_type = filters.NumberFilter(field_name='service_type')

    class Meta:
        model = UpcomingDueDates
        fields = ['service_type']


class BusinessContactPersonSerializer(BaseModelSerializer):
    class Meta:
        model = BusinessContactPersonDetails
        fields = '__all__'


class UserBusinessContactPersonsSerializer(BaseModelSerializer):
    contact_persons = BusinessContactPersonSerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'contact_persons']


class PasswordResetSerializer(BaseSerializer):
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


class UpdateUserTypeSerializer(BaseModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'client_type']


class UserSerializer(BaseModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'profile_picture','mobile_number', 'email']


class ProfileInformationSerializer(BaseModelSerializer):
    date_of_birth = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y"])

    class Meta:
        model = ProfileInformation
        fields = ['first_name', 'last_name', 'fathers_name', 'date_of_birth', 'gender', 'maritual_status']


class ProfileAddressSerializer(BaseModelSerializer):
    address_type_display = serializers.SerializerMethodField()
    rent_status_display = serializers.SerializerMethodField()

    class Meta:
        model = ProfileAddress
        fields = [
            'id', 'address_type', 'address_type_display', 'rent_status_display', 'door_no', 'permise_name',
            'street', 'area', 'city', 'state', 'pincode', 'country', 'rent_status', 'rental_agreement'
        ]
        extra_kwargs = {
            'rental_agreement': {'required': False, 'allow_null': True}
        }

    def get_address_type_display(self, obj):
        return obj.get_address_type_display()

    def get_rent_status_display(self, obj):
        return obj.get_rent_status_display()

    def validate(self, data):
        rent_status = data.get('rent_status')
        rental_agreement = data.get('rental_agreement')

        if rent_status == ProfileAddress.RENTED and not rental_agreement:
            raise serializers.ValidationError({
                "rental_agreement": "Rental agreement must be uploaded if the address is rented."
            })

        return data

    def create(self, validated_data):
        return super().create(validated_data)


class ProfileInformationUpdateSerializer(BaseModelSerializer):
    full_name = serializers.CharField(write_only=True)
    date_of_birth = serializers.CharField()
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = ProfileInformation
        fields = ['full_name', 'fathers_name', 'date_of_birth', 'gender', 'maritual_status',
                  'profile_picture']

    def validate_date_of_birth(self, value):
        try:
            return datetime.datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            raise serializers.ValidationError("Date of birth must be in format 'dd/mm/yyyy'.")

    def update(self, instance, validated_data):
        full_name = validated_data.pop('full_name', None)
        if full_name:
            name_parts = full_name.split()
            instance.first_name = name_parts[0]
            instance.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        instance.fathers_name = validated_data.get('fathers_name', instance.fathers_name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.maritual_status = validated_data.get('maritual_status', instance.maritual_status)

        profile_picture = validated_data.get('profile_picture', None)
        if profile_picture:
            instance.user.profile_picture = profile_picture
            instance.user.save()

        instance.save()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['full_name'] = f"{instance.first_name} {instance.last_name}".strip()
        ret['date_of_birth'] = instance.date_of_birth.strftime('%d/%m/%Y') if instance.date_of_birth else None
        ret['profile_picture'] = instance.user.profile_picture.url if instance.user.profile_picture else None
        return ret


class GovernmentIDSerializer(BaseModelSerializer):
    class Meta:
        model = GovernmentID
        fields = [
            'id', 'pan_no', 'pan_card', 'is_pan_verified',
            'aadhar_no', 'aadhar_card', 'is_aadhaar_verified',
            'driving_license_no', 'driving_license_card', 'driving_license_validity', 'is_driving_license_verified',
            'voter_id_no', 'voter_id_card', 'is_voter_id_verified',
            'ration_card_no', 'ration_card_file', 'is_ration_card_verified',
            'passport_no', 'passport_file', 'passport_validity', 'is_passport_verified'
        ]


class ProfileBankDetailsSerializer(BaseModelSerializer):
    class Meta:
        model = ProfileBankAccounts
        fields = ['id', 'account_no', 'ifsc_code', 'bank_name', 'type', 'is_primary']

    def __init__(self, *args, **kwargs):
        super(ProfileBankDetailsSerializer, self).__init__(*args, **kwargs)
        self.fields['is_primary'].required = False

    def validate(self, data):

        is_primary = data.get('is_primary', False)
        user = self.context['request'].user

        if is_primary:
            if self.instance and self.instance.is_primary == is_primary:
                return data

            existing_primary = ProfileBankAccounts.objects.filter(user=user, is_primary=True)

            if self.instance:
                existing_primary = existing_primary.exclude(id=self.instance.id)

            if existing_primary.exists():
                raise serializers.ValidationError("Only one primary bank account is allowed.")

        return data


class EmailUpdateOtpSerializer(BaseSerializer):
    otp_id = serializers.CharField()
    otp = serializers.CharField(max_length=4)

    def validate_otp(self, value):
        if len(value) != 4:
            raise serializers.ValidationError("OTP must be 4 digits.")
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only numbers.")
        return value

    def validate_otp_id(self, value):
        try:
            decoded_id = self.decode_id(value)
            return decoded_id
        except Exception as e:
            raise serializers.ValidationError(f"Invalid OTP ID: {str(e)}")





