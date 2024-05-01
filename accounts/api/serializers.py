from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from rest_framework import serializers, request, status
from django.contrib.auth.models import User
from rest_framework.response import Response

from accounts.models import User, WorkOrder, ServicePages, WorkOrderDocument, WorkOrderDownloadDocument, \
    WorkorderPayment, UpcomingDueDates


class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(required=True)
    password = serializers.CharField(max_length=128,required=True)

    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')
        password = attrs.get('password')
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
    mobile_regex = RegexValidator(
        regex=r'^[1-9][0-9]{9}$',
        message="Please enter a valid mobile number format."
    )
    mobile_number = serializers.CharField(validators=[mobile_regex], max_length=10, min_length=10, required=True)
    full_name = serializers.CharField(required=True)
    date_of_birth = serializers.DateField(format='%d-%m-%Y', input_formats=['%d-%m-%Y'], required=True)
    password = serializers.CharField(max_length=128, required=True)
    state = serializers.ChoiceField(choices=User.STATES_CHOICES, required=True)
    email = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')
        if not mobile_number:
            raise serializers.ValidationError("Mobile Number is required field.")
        full_name = attrs.get('full_name')
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
    date_of_birth = serializers.DateField()
    state = serializers.ChoiceField(choices=User.STATES_CHOICES)
    email = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False)
    confirm_password = serializers.CharField(required=False)
    client_type = serializers.ChoiceField(choices=User.CLIENT_TYPE_CHOICES)
    industry_type = serializers.ChoiceField(choices=User.INDUSTRY_TYPE_CHOICES)
    nature_of_business = serializers.ChoiceField(choices=User.NATURE_OF_BUSINESS_CHOICES)
    contact_person = serializers.CharField(max_length=255, required=False)
    job_title = serializers.CharField(max_length=255, required=False)
    contact_person_phone_number = serializers.CharField(max_length=10, required=False)
    contact_mail = serializers.CharField(max_length=255)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.password = make_password(validated_data['password'])
        instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        if 'date_of_birth' in validated_data:
            instance.date_of_birth = validated_data['date_of_birth']
        instance.state = validated_data.get('state', instance.state)
        if 'email' in validated_data:
            instance.email = validated_data['email']
        instance.client_type = validated_data.get('client_type', instance.client_type)
        instance.industry_type = validated_data.get('industry_type', instance.industry_type)
        instance.nature_of_business = validated_data.get('nature_of_business', instance.nature_of_business)
        instance.contact_person = validated_data.get('contact_person', instance.contact_person)
        instance.job_title = validated_data.get('job_title', instance.job_title)
        instance.contact_person_phone_number = validated_data.get('contact_person_phone_number',
                                                                  instance.contact_person_phone_number)
        instance.contact_email = validated_data.get('contact_email', instance.contact_email)
        instance.save()
        return instance


class WorkOrderSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')
    service_id = serializers.IntegerField(write_only=True)
    service_name = serializers.SerializerMethodField()
    required_documents_list = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ('user', 'service', 'service_name')

    def get_required_documents_list(self, obj):
        if obj.service:
            return obj.service.get_required_documents_list()
        return []

    def get_service_name(self, obj):
        return obj.service.service_title if obj.service else None

    def validate_service_id(self, value):
        try:
            service = ServicePages.objects.get(id=value)
            self.context['service'] = service
        except ServicePages.DoesNotExist:
            raise serializers.ValidationError(f"Service with ID {value} does not exist.")
        return value

    def create(self, validated_data):
        validated_data['service'] = self.context.get('service')
        validated_data['user'] = self.context['request'].user
        return WorkOrder.objects.create(**validated_data)


class WorkOrderDocumentsUploadSerializer(serializers.ModelSerializer):
    work_order_id = serializers.IntegerField(write_only=True)
    document_name = serializers.CharField(max_length=255)
    document_file = serializers.FileField()

    class Meta:
        model = WorkOrderDocument
        fields=['work_order_id', 'document_name', 'document_file',  'uploaded_by_beyondtax']

    def validate_work_order_id(self, value):
        try:
            work_order_id = WorkOrder.objects.get(id=value)
        except WorkOrder.DoesNotExist:
            raise serializers.ValidationError(f"Work order with ID {value} does not exist.")
        self.context['work_order'] = work_order_id
        return value

    def validate_document_name(self, value):
        work_order = self.context.get('work_order')
        if not work_order:
            raise serializers.ValidationError("Work order must be provided to validate document name.")
        required_docs_list = work_order.service.get_required_documents_list()
        if value not in required_docs_list:
            raise serializers.ValidationError(
                f"Document name '{value}' is not in the required documents list: {required_docs_list}")

        return value


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

    def get_full_name(self, obj):
        first_name = obj.first_name or ""
        last_name = obj.last_name or ""
        return f"{first_name} {last_name}".strip()


class WorkOrderDownloadDocumentSerializer(serializers.Serializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderDownloadDocument
        fields = ['id', 'work_order', 'download_document', 'description', 'document_url']

    def get_document_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.download_document.url)
        return None


class WorkOrderDownloadDocumentListSerializer(serializers.Serializer):
    document_url = serializers.SerializerMethodField()
    wo_dept = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderDownloadDocument
        fields = ['id', 'work_order', 'download_document', 'description', 'wo_dept',
                  'document_url']

    def get_document_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.download_document.url)
        return None

    def get_wo_dept(self, obj):
        return obj.work_order.wo_dept if obj.work_order else None


class WorkorderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkorderPayment
        fields = ['work_order', 'bank_account', 'ifsc_code', 'recipient_name', 'qr_code_url',
                  'amount_due']


class UpcomingDueDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpcomingDueDates
        fields = ['data']
