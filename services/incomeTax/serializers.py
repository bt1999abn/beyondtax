from django.core.validators import RegexValidator
from rest_framework import serializers
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxReturnYears, \
    IncomeTaxReturn


class IncomeTaxAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeTaxAddress
        fields = ['door_no', 'permise_name', 'street', 'area', 'pincode', 'country', 'state', 'city']


class IncomeTaxProfileSerializer(serializers.Serializer):
    mobile_regex = RegexValidator(
        regex=r'^[1-9][0-9]{9}$',
        message="Please enter a valid mobile number format."
    )

    first_name = serializers.CharField(max_length=255, required=True)
    middle_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=255, required=True)
    date_of_birth = serializers.DateField(format='%d-%m-%Y', input_formats=['%d-%m-%Y'], required=True)
    fathers_name = serializers.CharField(max_length=255, required=True)
    gender = serializers.ChoiceField(choices=IncomeTaxProfile.GENDER_CHOICES,
                                     required=True)
    marital_status = serializers.ChoiceField(choices=IncomeTaxProfile.MARRIED_STATUS_CHOICES,
                                             required=True)
    email = serializers.EmailField(required=True)
    mobile_number = serializers.CharField(validators=[mobile_regex], max_length=10, min_length=10, required=True)
    aadhar_no = serializers.CharField(max_length=12, required=True)
    aadhar_enrollment_no = serializers.CharField(max_length=29, required=True)
    pan_no = serializers.CharField(max_length=10, required=True)
    residential_status = serializers.CharField(max_length=50, required=True)
    address = IncomeTaxAddressSerializer(required=True)

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        income_tax_profile = IncomeTaxProfile.objects.create(**validated_data)
        IncomeTaxAddress.objects.create(income_tax=income_tax_profile, **address_data)
        return income_tax_profile

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        if address_data:
            IncomeTaxAddress.objects.filter(income_tax=instance).update(**address_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['profile_title'] = f"{instance.first_name} {instance.last_name}"
        return representation


class IncomeTaxBankDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = IncomeTaxBankDetails
        fields = ['account_no', 'ifsc_code', 'bank_name', 'type','income_tax']

    def create(self, validated_data):
        return IncomeTaxBankDetails.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class IncomeTaxReturnYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeTaxReturnYears
        fields = ('id','name','start_date', 'end_date', 'due_date', 'status')


class IncomeTaxReturnSerializer(serializers.ModelSerializer):
    income_tax_return_year = IncomeTaxReturnYearSerializer()

    class Meta:
        model = IncomeTaxReturn
        fields = ('id', 'user', 'income_tax_return_year', 'status')