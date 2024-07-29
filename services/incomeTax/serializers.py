from datetime import datetime

from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxReturnYears, \
    IncomeTaxReturn, ResidentialStatusQuestions, ResidentialStatusAnswer, SalaryIncome, RentalIncome, BuyerDetails, \
    CapitalGains, TdsOrTcsDeduction, SelfAssesmentAndAdvanceTaxPaid, IncomeFromBetting, DividendIncome, \
    InterestOnItRefunds, ExemptIncome, BusinessIncome, AgricultureIncome, LandDetails, Deductions, InterestIncome


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
            'email', 'residential_status', 'income_tax_bankdetails', 'address', 'answers', 'created_at', 'updated_at',

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
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = IncomeTaxReturn
        fields = ('id', 'user', 'income_tax_return_year', 'status', 'status_display')


class ResidentialStatusQuestionsSerializer(serializers.ModelSerializer):
    options_type_name = serializers.SerializerMethodField()

    class Meta:
        model = ResidentialStatusQuestions
        fields = ['id', 'question', 'options', 'options_type_name']

    def get_options_type_name(self, obj):
        return obj.get_options_type_display()


class SalaryIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryIncome
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RentalIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalIncome
        fields = "__all__"


class BuyerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerDetails
        fields = "__all__"


class CapitalGainsSerializer(serializers.ModelSerializer):
    buyer_details = BuyerDetailsSerializer(many=True, required=False)

    class Meta:
        model = CapitalGains
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(CapitalGainsSerializer, self).__init__(*args, **kwargs)
        if 'asset_type' in self.initial_data:
            asset_type = int(self.initial_data['asset_type'])
            if asset_type == CapitalGains.HouseProperty:
                self.fields['property_door_no'].required = True
                self.fields['property_city'].required = True
                self.fields['property_area'].required = True
                self.fields['property_pin'].required = True
                self.fields['property_state'].required = True
                self.fields['property_country'].required = True
                self.fields['buyer_details'].required = True
            elif asset_type == CapitalGains.ListedSharesOrMutualFunds:
                self.fields['property_door_no'].required = False
                self.fields['property_city'].required = False
                self.fields['property_area'].required = False
                self.fields['property_pin'].required = False
                self.fields['property_state'].required = False
                self.fields['property_country'].required = False
                self.fields['buyer_details'].required = False

    def create(self, validated_data):
        buyer_details_data = validated_data.pop('buyer_details', [])
        capital_gains = CapitalGains.objects.create(**validated_data)
        for buyer_data in buyer_details_data:
            BuyerDetails.objects.create(capital_gains=capital_gains, **buyer_data)
        return capital_gains

    def update(self, instance, validated_data):
        buyer_details_data = validated_data.pop('buyer_details', [])
        instance = super().update(instance, validated_data)
        for buyer_data in buyer_details_data:
            BuyerDetails.objects.update_or_create(
                capital_gains=instance,
                id=buyer_data.get('id'),
                defaults=buyer_data
            )
        return instance


class LandDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandDetails
        fields = "__all__"


class AgricultureIncomeSerializer(serializers.ModelSerializer):
    land_details = LandDetailsSerializer(many=True, required=False)

    class Meta:
        model = AgricultureIncome
        fields = "__all__"

    def create(self, validated_data):
        land_details_data = validated_data.pop('land_details', [])
        agriculture_income = AgricultureIncome.objects.create(**validated_data)
        for land_data in land_details_data:
            LandDetails.objects.create(agriculture_income=agriculture_income, **land_data)
        return agriculture_income

    def update(self, instance, validated_data):
        land_details_data = validated_data.pop('land_details', [])
        instance = super().update(instance, validated_data)

        for land_data in land_details_data:
            LandDetails.objects.update_or_create(
                agriculture_income=instance,
                id=land_data.get('id'),
                defaults=land_data
            )
        return instance


class BusinessIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessIncome
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ExemptIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExemptIncome
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AgricultureAndExemptIncomeSerializer(serializers.ModelSerializer):
    agriculture_incomes = AgricultureIncomeSerializer(many=True, required=False)
    exempt_incomes = ExemptIncomeSerializer(many=True, required=False)

    class Meta:
        fields = ['agriculture_incomes', 'exempt_incomes']


class InterestIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestIncome
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class InterestOnItRefundsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestOnItRefunds
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DividendIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendIncome
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class IncomeFromBettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeFromBetting
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class OtherIncomesSerializer(serializers.ModelSerializer):
    interest_incomes = InterestIncomeSerializer(many=True, required=False)
    interest_on_it_refunds = InterestOnItRefundsSerializer(many=True, required=False)
    dividend_incomes = DividendIncomeSerializer(many=True, required=False)
    income_from_betting = IncomeFromBettingSerializer(many=True, required=False)

    class Meta:
        fields = ['interest_incomes', 'interest_on_it_refunds', 'dividend_incomes', 'income_from_betting']


class TdsOrTcsDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdsOrTcsDeduction
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SelfAssesmentAndAdvanceTaxPaidSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfAssesmentAndAdvanceTaxPaid
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TaxPaidSerializer(serializers.ModelSerializer):
    tds_or_tcs_deductions = TdsOrTcsDeductionSerializer(many=True, required=False)
    self_assessment_and_advance_tax_paid = SelfAssesmentAndAdvanceTaxPaidSerializer(many=True, required=False)

    class Meta:
        fields = ['tds_or_tcs_deductions', 'self_assessment_and_advance_tax_paid']


class DeductionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deductions
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance