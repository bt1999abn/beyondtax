from datetime import datetime

from django.core.validators import RegexValidator
from rest_framework import serializers
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxReturnYears, \
    IncomeTaxReturn


class IncomeTaxBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeTaxBankDetails
        fields = ['id', 'account_no', 'ifsc_code', 'bank_name', 'type', 'created_at']
        extra_kwargs = {
            'account_no': {'required': True},
            'ifsc_code': {'required': True},
            'bank_name': {'required': True},
            'type': {'required': True},
        }


class IncomeTaxAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeTaxAddress
        fields = ['door_no', 'permise_name', 'street', 'area', 'city', 'state', 'pincode', 'country']
        extra_kwargs = {
            'door_no': {'required': True},
            'permise_name': {'required': True},
            'street': {'required': True},
            'area': {'required': True},
            'city': {'required': True},
            'state': {'required': True},
            'pincode': {'required': True},
            'country': {'required': True},
        }


class IncomeTaxProfileSerializer(serializers.ModelSerializer):
    income_tax_bankdetails = IncomeTaxBankDetailsSerializer(many=True, required=False)
    address = IncomeTaxAddressSerializer(required=False)
    date_of_birth = serializers.CharField(required=True)
    mobile_number = serializers.CharField(validators=[RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message="Enter a valid mobile number"
    )])

    class Meta:
        model = IncomeTaxProfile
        fields = [
            'id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'fathers_name',
            'gender', 'marital_status', 'aadhar_no', 'aadhar_enrollment_no', 'pan_no','mobile_number',
            'email', 'residential_status', 'income_tax_bankdetails', 'address', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'middle_name': {'required': True},
            'last_name': {'required': True},
            'date_of_birth': {'required': True},
            'fathers_name': {'required': True},
            'gender': {'required': True},
            'marital_status': {'required': True},
            'aadhar_no': {'required': True},
            'aadhar_enrollment_no': {'required': True},
            'pan_no': {'required': True},
            'mobile_number': {'required': True},
            'email': {'required': True},
            'residential_status': {'required': True},
        }

    def validate_date_of_birth(self, value):
        try:
            return datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError:
            raise serializers.ValidationError("Date of birth must be in the format dd-mm-yyyy")

    def create(self, validated_data):
        bank_details_data = validated_data.pop('income_tax_bankdetails', [])
        address_data = validated_data.pop('address', None)
        income_tax_profile = IncomeTaxProfile.objects.create(**validated_data)

        for bank_detail_data in bank_details_data:
            IncomeTaxBankDetails.objects.create(income_tax=income_tax_profile, **bank_detail_data)

        if address_data:
            IncomeTaxAddress.objects.create(income_tax=income_tax_profile, **address_data)

        return income_tax_profile

    def update(self, instance, validated_data):
        bank_details_data = validated_data.pop('income_tax_bankdetails', [])
        address_data = validated_data.pop('address', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if address_data:
            if hasattr(instance, 'address'):
                address_instance = instance.address
                for attr, value in address_data.items():
                    setattr(address_instance, attr, value)
                address_instance.save()
            else:
                IncomeTaxAddress.objects.create(income_tax=instance, **address_data)

        IncomeTaxBankDetails.objects.filter(income_tax=instance).delete()
        for bank_detail_data in bank_details_data:
            IncomeTaxBankDetails.objects.create(income_tax=instance, **bank_detail_data)

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