from datetime import datetime

from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxReturnYears, \
    IncomeTaxReturn, ResidentialStatusQuestions, ResidentialStatusAnswer


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
            'street': {'required': True},
            'area': {'required': True},
            'city': {'required': True},
            'state': {'required': True},
            'pincode': {'required': True},
            'country': {'required': True},
        }


class ResidentialStatusAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialStatusAnswer
        fields = ['question', 'answer_text']


class IncomeTaxProfileSerializer(serializers.ModelSerializer):
    income_tax_bankdetails = IncomeTaxBankDetailsSerializer(many=True, required=False)
    address = IncomeTaxAddressSerializer(required=False)
    answers = ResidentialStatusAnswerSerializer(many=True, required=False)
    date_of_birth = serializers.CharField(required=True)
    mobile_number = serializers.CharField(validators=[RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message="Enter a valid mobile number"
    )])

    class Meta:
        model = IncomeTaxProfile
        fields = [
            'id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'fathers_name',
            'gender', 'marital_status', 'aadhar_no', 'aadhar_enrollment_no', 'pan_no', 'mobile_number',
            'email', 'residential_status', 'income_tax_bankdetails', 'address', 'answers', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        if not data.get('aadhar_no') and not data.get('aadhar_enrollment_no'):
            raise serializers.ValidationError("Either 'aadhar_no' or 'aadhar_enrollment_no' must be provided.")
        return data

    def validate_date_of_birth(self, value):
        try:
            return datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError:
            raise serializers.ValidationError("Date of birth must be in the format dd-mm-yyyy")

    def create(self, validated_data):
        user = self.context['request'].user
        bank_details_data = validated_data.pop('income_tax_bankdetails', [])
        address_data = validated_data.pop('address', None)
        answers_data = validated_data.pop('answers', [])

        income_tax_profile = IncomeTaxProfile.objects.create(user=user, **validated_data)

        for bank_detail_data in bank_details_data:
            IncomeTaxBankDetails.objects.create(income_tax=income_tax_profile, **bank_detail_data)

        if address_data:
            IncomeTaxAddress.objects.create(income_tax=income_tax_profile, **address_data)

        for answer_data in answers_data:
            ResidentialStatusAnswer.objects.create(income_tax=income_tax_profile, **answer_data)
        next_question_data = self.process_answers(income_tax_profile, answers_data)
        return income_tax_profile, next_question_data

    def update(self, instance, validated_data):
        bank_details_data = validated_data.pop('income_tax_bankdetails', [])
        address_data = validated_data.pop('address', None)
        answers_data = validated_data.pop('answers', [])

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

        ResidentialStatusAnswer.objects.filter(income_tax=instance).delete()
        for answer_data in answers_data:
            ResidentialStatusAnswer.objects.create(income_tax=instance, **answer_data)
        next_question_data = self.process_answers(instance, answers_data)
        return instance, next_question_data

    def process_answers(self, profile, answers_data):
        final_status = None
        next_question_id = None

        for answer_data in answers_data:
            current_question_id = answer_data.get('question').id
            answer_text = answer_data.get('answer_text')

            if current_question_id == 8:
                if answer_text == "Less than 60 days":
                    final_status = IncomeTaxProfile.NonResidentIndian
                elif answer_text == "182 days or More":
                    final_status = IncomeTaxProfile.IndianResident
                elif answer_text == "60 days - 119 days":
                    next_question_id = 9
                elif answer_text == "120 days - 181 days":
                    next_question_id = 15
            elif current_question_id == 9:
                if answer_text == "Yes":
                    final_status = IncomeTaxProfile.NonResidentIndian
                elif answer_text == "No":
                    next_question_id = 10
            elif current_question_id == 10:
                if answer_text == "Yes":
                    next_question_id = 11
                elif answer_text == "No":
                    final_status = IncomeTaxProfile.NonResidentIndian
            elif current_question_id == 11:
                if answer_text == "Yes":
                    next_question_id = 12
                elif answer_text == "No":
                    final_status = IncomeTaxProfile.NonResidentIndian
            elif current_question_id == 12:
                if answer_text == "Yes":
                    final_status = IncomeTaxProfile.IndianResidentButOrdinary
                elif answer_text == "No":
                    final_status = IncomeTaxProfile.IndianResidentButNotOrdinary
            elif current_question_id == 13:
                if answer_text == "Person of Indian origin but a citizen of another country":
                    next_question_id = 14
                elif answer_text == "Foreign citizen visiting or coming to India for employment":
                    next_question_id = 9
            elif current_question_id == 14:
                if answer_text == "No":
                    final_status = IncomeTaxProfile.NonResidentIndian
                elif answer_text == "Yes":
                    next_question_id = 10

            if final_status is not None:
                profile.residential_status = final_status
                profile.save()
                return {"status": dict(IncomeTaxProfile.RESIDENTIAL_STATUS_CHOICES).get(final_status)}

            if next_question_id is not None:
                next_question = get_object_or_404(ResidentialStatusQuestions, id=next_question_id)
                next_question_data = self.build_question_tree(next_question)
                return next_question_data

        return {"status": None}

    def build_question_tree(self, question):
        question_data = {
            'id': question.id,
            'question': question.question,
            'options': {option['name']: option['next_question_id'] for option in question.options},
            'next_question': {}
        }

        for option in question.options:
            if option['next_question_id']:
                next_question = get_object_or_404(ResidentialStatusQuestions, id=option['next_question_id'])
                question_data['next_question'][option['name']] = self.build_question_tree(next_question)
            else:
                question_data['next_question'][option['name']] = None

        return question_data


class IncomeTaxReturnYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeTaxReturnYears
        fields = ('id','name','start_date', 'end_date', 'due_date', 'status')


class IncomeTaxReturnSerializer(serializers.ModelSerializer):
    income_tax_return_year = IncomeTaxReturnYearSerializer()

    class Meta:
        model = IncomeTaxReturn
        fields = ('id', 'user', 'income_tax_return_year', 'status')


class ResidentialStatusQuestionsSerializer(serializers.ModelSerializer):
    options_type_name = serializers.SerializerMethodField()

    class Meta:
        model = ResidentialStatusQuestions
        fields = ['id', 'question', 'options', 'options_type_name']

    def get_options_type_name(self, obj):
        return obj.get_options_type_display()