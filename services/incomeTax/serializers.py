import re
from datetime import datetime, date
import fitz
from django.core.validators import RegexValidator
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxReturnYears, \
    IncomeTaxReturn, ResidentialStatusQuestions, ResidentialStatusAnswer, SalaryIncome, RentalIncome, BuyerDetails, \
    CapitalGains, TdsOrTcsDeduction, SelfAssesmentAndAdvanceTaxPaid, IncomeFromBetting, DividendIncome, \
    InterestOnItRefunds, ExemptIncome, BusinessIncome, AgricultureIncome, LandDetails, Deductions, InterestIncome, \
    Computations
from shared.libs.hashing import AlphaId
from shared.rest.serializers import BaseModelSerializer, BaseSerializer


class IncomeTaxBankDetailsSerializer(BaseModelSerializer):
    class Meta:
        model = IncomeTaxBankDetails
        fields = ['id', 'account_no', 'ifsc_code', 'bank_name', 'type', 'created_at']
        extra_kwargs = {
            'account_no': {'required': True},
            'ifsc_code': {'required': True},
            'bank_name': {'required': True},
            'type': {'required': True},
        }


class IncomeTaxAddressSerializer(BaseModelSerializer):
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


class ResidentialStatusAnswerSerializer(BaseModelSerializer):
    class Meta:
        model = ResidentialStatusAnswer
        fields = ['question', 'answer_text']


class IncomeTaxProfileSerializer(BaseModelSerializer):
    income_tax_bankdetails = IncomeTaxBankDetailsSerializer(many=True, required=False)
    address = IncomeTaxAddressSerializer(required=False)
    answers = ResidentialStatusAnswerSerializer(many=True, required=False)
    date_of_birth = serializers.DateField(required=True)
    mobile_number = serializers.CharField(validators=[RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message="Enter a valid mobile number"
    )])

    class Meta:
        model = IncomeTaxProfile
        fields = [
            'id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'fathers_name',
            'gender', 'marital_status', 'aadhar_no', 'aadhar_enrollment_no', 'pan_no', 'mobile_number',
            'email', 'residential_status', 'income_tax_bankdetails', 'address', 'answers', 'created_at', 'updated_at',
            'is_pan_verified', 'is_data_imported'
        ]

    def validate(self, data):
        if not data.get('aadhar_no') and not data.get('aadhar_enrollment_no'):
            raise serializers.ValidationError("Either 'aadhar_no' or 'aadhar_enrollment_no' must be provided.")
        if 'pan_no' in data and self.instance and data['pan_no'] != self.instance.pan_no:
            raise serializers.ValidationError("You are not allowed to update the PAN number.")
        return data

    def validate_date_of_birth(self, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%m-%Y").date()
            except ValueError:
                raise serializers.ValidationError("Date of birth must be in the format dd-mm-yyyy")
        elif isinstance(value, date):
            return value
        else:
            raise serializers.ValidationError("Invalid type for date_of_birth")

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

        return instance

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


class IncomeTaxReturnYearSerializer(BaseModelSerializer):
    class Meta:
        model = IncomeTaxReturnYears
        fields = ('id','name','start_date', 'end_date', 'due_date', 'status')


class IncomeTaxReturnSerializer(BaseModelSerializer):
    income_tax_return_year = IncomeTaxReturnYearSerializer()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = IncomeTaxReturn
        fields = ('id', 'user', 'income_tax_return_year', 'status', 'status_display')


class ResidentialStatusQuestionsSerializer(BaseModelSerializer):
    options_type_name = serializers.SerializerMethodField()

    class Meta:
        model = ResidentialStatusQuestions
        fields = ['id', 'question', 'options', 'options_type_name']

    def get_options_type_name(self, obj):
        return obj.get_options_type_display()


class SalaryIncomeSerializer(BaseModelSerializer):
    class Meta:
        model = SalaryIncome
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RentalIncomeSerializer(BaseModelSerializer):
    class Meta:
        model = RentalIncome
        fields = "__all__"
        extra_kwargs = {
            'standard_deduction': {'required': False},
            'net_rental_income': {'required': False}
        }

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)


class BuyerDetailsSerializer(BaseModelSerializer):
    class Meta:
        model = BuyerDetails
        fields = "__all__"
        extra_kwargs = {'capital_gains': {'required': False}}


class CapitalGainsSerializer(BaseModelSerializer):
    buyer_details = BuyerDetailsSerializer(many=True, required=False)

    class Meta:
        model = CapitalGains
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        for buyer in data.get('buyer_details', []):
            if 'id' in buyer:
                buyer['id'] = AlphaId.decode(buyer['id'])
        return super().to_internal_value(data)

    def validate(self, data):
        asset_type = data.get('asset_type')
        term_type = data.get('term_type', None)

        if asset_type == CapitalGains.HouseProperty:
            required_fields = ['property_door_no', 'property_city', 'property_area', 'property_pin', 'property_state', 'property_country']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({field: f"{field} is required for House Property asset type."})
            if 'buyer_details' in data:
                if not data['buyer_details']:
                    raise serializers.ValidationError({"buyer_details": "Buyer details are required for House Property asset type."})
        elif asset_type == CapitalGains.ListedSharesOrMutualFunds:
            if term_type == CapitalGains.ShortTerm:
                if data.get('isn_code') is not None or data.get('fair_value_per_unit') is not None:
                    raise serializers.ValidationError({"isn_code": "ISN Code should not be provided for Short Term.", "fair_value_per_unit": "Fair Value Per Unit should not be provided for Short Term."})
            elif term_type == CapitalGains.LongTerm:
                if data.get('no_of_units') is not None:
                    raise serializers.ValidationError({"no_of_units": "No of Units should not be provided for Long Term."})
        return data

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


class LandDetailsSerializer(BaseModelSerializer):
    class Meta:
        model = LandDetails
        fields = "__all__"


class AgricultureIncomeSerializer(BaseModelSerializer):
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


class BusinessIncomeSerializer(BaseModelSerializer):
    class Meta:
        model = BusinessIncome
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ExemptIncomeSerializer(BaseModelSerializer):
    class Meta:
        model = ExemptIncome
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AgricultureAndExemptIncomeSerializer(BaseModelSerializer):
    agriculture_incomes = AgricultureIncomeSerializer(many=True, required=False)
    exempt_incomes = ExemptIncomeSerializer(many=True, required=False)

    class Meta:
        fields = ['agriculture_incomes', 'exempt_incomes']


class InterestIncomeSerializer(BaseModelSerializer):
    class Meta:
        model = InterestIncome
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class InterestOnItRefundsSerializer(BaseModelSerializer):
    class Meta:
        model = InterestOnItRefunds
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DividendIncomeSerializer(BaseModelSerializer):
    class Meta:
        model = DividendIncome
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class IncomeFromBettingSerializer(BaseModelSerializer):
    class Meta:
        model = IncomeFromBetting
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class OtherIncomesSerializer(BaseModelSerializer):
    interest_incomes = InterestIncomeSerializer(many=True, required=False)
    interest_on_it_refunds = InterestOnItRefundsSerializer(many=True, required=False)
    dividend_incomes = DividendIncomeSerializer(many=True, required=False)
    income_from_betting = IncomeFromBettingSerializer(many=True, required=False)

    class Meta:
        fields = ['interest_incomes', 'interest_on_it_refunds', 'dividend_incomes', 'income_from_betting']


class TdsOrTcsDeductionSerializer(BaseModelSerializer):
    class Meta:
        model = TdsOrTcsDeduction
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SelfAssesmentAndAdvanceTaxPaidSerializer(BaseModelSerializer):
    class Meta:
        model = SelfAssesmentAndAdvanceTaxPaid
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TaxPaidSerializer(BaseModelSerializer):
    tds_or_tcs_deductions = TdsOrTcsDeductionSerializer(many=True, required=False)
    self_assessment_and_advance_tax_paid = SelfAssesmentAndAdvanceTaxPaidSerializer(many=True, required=False)

    class Meta:
        fields = ['tds_or_tcs_deductions', 'self_assessment_and_advance_tax_paid']


class DeductionsSerializer(BaseModelSerializer):
    class Meta:
        model = Deductions
        fields = "__all__"

    def to_internal_value(self, data):
        if 'id' in data:
            data['id'] = AlphaId.decode(data['id'])
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AISPdfUploadSerializer(BaseSerializer):
    ais_pdf = serializers.FileField()

    def extract_text_from_pdf(self, pdf_file, password):
        try:
            pdf_file.seek(0)
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            if not doc.authenticate(password):
                raise Exception("Invalid password for PDF document")
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text")
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    def extract_data_from_text(self, text):
        extracted_data = {
            "salary": [],
            "rent_received": [],
            "dividends": [],
            "business_receipts": [],
            "interest_income": []
        }

        patterns = {
            "salary": re.compile(
                r"(\d+)\s+TDS-192\s+Salary received.*?\s+([A-Z\s]+ \(.*?\))\s+(\d+)\s+([\d,]+)",
                re.S
            ),
            "rent_received": re.compile(
                r"(\d+)\s+TDS-194I\(b\)\s+Rent received.*?\s+([A-Z\s]+ \(.*?\))\s+(\d+)\s+([\d,]+)",
                re.S
            ),
            "dividends": re.compile(
                r"(\d+)\s+TDS-194\[K\]?\s+Dividend received.*?\s+([A-Z\s]+ \(.*?\))\s+(\d+)\s+([\d,]+)",
                re.S
            ),
            "business_receipts": re.compile(
                r"(\d+)\s+TDS-194J\s+Receipt of fees.*?\s+([A-Z\s]+ \(.*?\))\s+(\d+)\s+([\d,]+)",
                re.S
            ),
            "interest_income": re.compile(
                r"(\d+)\s+SFT-016\(SB\)\s+Interest income.*?\s+([A-Z\s]+ \(.*?\))\s+(\d+)\s+([\d,]+)",
                re.S
            )
        }

        for key, pattern in patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                extracted_data[key].append({
                    "sr_no": int(match[0]),
                    "information_source": match[1],
                    "amount": match[3].replace(',', '')
                })

        return extracted_data

    def save_extracted_data(self, extracted_data, income_tax_return):
        income_tax_profile = income_tax_return.user.income_tax_profile
        saved_data = {"salary": [], "rent_received": [], "business_receipts": [], "dividends": [], "interest_income": []}

        for item in extracted_data["salary"]:
            salary_income, _ = SalaryIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                employer_name=item["information_source"],
                defaults={
                    "gross_salary": item["amount"],
                    "employer_category": SalaryIncome.Private,
                    "tan": "",
                    "tds_deduction": 0.0,
                    "income_reported": 0.0,
                    "upload_form_type": SalaryIncome.Form16,
                    "upload_form_file": None,
                    "basic_salary_component": 0.0,
                    "hra_component": 0.0,
                    "annual_rent_paid": 0.0,
                    "do_you_live_in_these_cities": False
                }
            )
            saved_data["salary"].append(salary_income)

        for item in extracted_data["rent_received"]:
            rental_income, _ = RentalIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                tenant_name=item["information_source"],
                defaults={
                    "annual_rent": item["amount"],
                    "occupancy_status": RentalIncome.LetOut,
                    "tenant_aadhar": "",
                    "tenant_pan": "",
                    "property_door_no": "",
                    "property_area": "",
                    "property_city": "",
                    "property_pincode": "",
                    "property_state": "",
                    "property_country": "",
                    "property_tax_paid": 0.0,
                    "interest_on_home_loan_dcp": 0.0,
                    "interest_on_home_loan_pc": 0.0,
                    "ownership_percent": 100
                }
            )
            saved_data["rent_received"].append(rental_income)

        for item in extracted_data["business_receipts"]:
            business_income, _ = BusinessIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                business_name=item["information_source"],
                defaults={
                    "gross_receipt_cheq_neft_rtgs_turnover": item["amount"],
                    "business_income_type": "44AD",
                    "industry": BusinessIncome.ITServices,
                    "nature_of_business": "",
                    "description": "",
                    "gross_receipt_cheq_neft_rtgs_profit": 0.0,
                    "gross_receipt_cash_upi_turnover": 0.0,
                    "gross_receipt_cash_upi_profit": 0.0,
                    "fixed_asset": 0.0,
                    "inventory": 0.0,
                    "receivebles": 0.0,
                    "loans_and_advances": 0.0,
                    "investments": 0.0,
                    "cash_in_hand": 0.0,
                    "bank_balance": 0.0,
                    "other_assets": 0.0,
                    "capital": 0.0,
                    "secured_loans": 0.0,
                    "payables": 0.0,
                    "unsecured_loans": 0.0,
                    "advances": 0.0,
                    "other_liabilities": 0.0
                }
            )
            saved_data["business_receipts"].append(business_income)

        for item in extracted_data["dividends"]:
            dividend_income, _ = DividendIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                particular=item["information_source"],
                defaults={
                    "amount": item["amount"],
                    "description": ""
                }
            )
            saved_data["dividends"].append(dividend_income)

        for item in extracted_data["interest_income"]:
            interest_income, _ = InterestIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                description=item["information_source"],
                defaults={
                    "interest_amount": item["amount"],
                    "interest_income_type": InterestIncome.SavingsBankAccount
                }
            )
            saved_data["interest_income"].append(interest_income)

        return saved_data

    def save(self):
        ais_pdf = self.validated_data.get('ais_pdf')
        income_tax_return = self.context['income_tax_return']
        pan_no = income_tax_return.user.income_tax_profile.pan_no
        date_of_birth = income_tax_return.user.income_tax_profile.date_of_birth.strftime('%d%m%Y')
        password = f"{pan_no.lower()}{date_of_birth}"
        pdf_text = self.extract_text_from_pdf(ais_pdf, password)
        if not pdf_text:
            raise serializers.ValidationError("Unable to extract text from the uploaded AIS file.")

        extracted_data = self.extract_data_from_text(pdf_text)
        return self.save_extracted_data(extracted_data, income_tax_return)


class TdsPdfSerializer(BaseSerializer):
    tds_pdf = serializers.FileField()

    def validate(self, data):
        income_tax_return_id = self.context['income_tax_return_id']
        try:
            income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=self.context['request'].user)
        except IncomeTaxReturn.DoesNotExist:
            raise serializers.ValidationError("IncomeTaxReturn not found")
        data['income_tax_return'] = income_tax_return
        return data

    def create(self, validated_data):
        tds_pdf = validated_data.get('tds_pdf')
        income_tax_return = validated_data.get('income_tax_return')
        income_tax_profile = income_tax_return.user.income_tax_profile
        pan_number = income_tax_profile.pan_no.lower()
        date_of_birth = income_tax_profile.date_of_birth.strftime("%d%m%Y")
        pdf_password = f"{pan_number}{date_of_birth}"
        extracted_data = self.extract_tds_details_from_pdf(tds_pdf, pdf_password)
        saved_records = []
        for item in extracted_data:
            tds_or_tcs, _ = TdsOrTcsDeduction.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                name_of_deductor=item['name_of_deductor'],
                tan=item['tan'],
                defaults={
                    "gross_receipts": item['gross_receipts'],
                    "tds_or_tcs_amount": item['tds_or_tcs_amount'],
                    "section": item['section']
                }
            )
            saved_records.append(tds_or_tcs)
        return saved_records

    def extract_tds_details_from_pdf(self, pdf_file, password):
        try:
            pdf_file.seek(0)
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            if not doc.authenticate(password):
                raise Exception("Invalid password for PDF document")
            extracted_data = []
            last_section = None
            pattern_details = re.compile(
                r"(\d+)\s+([A-Z\s]+)\s+([A-Z0-9]+)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)",
                re.S
            )
            pattern_section = re.compile(
                r"Section\s+(\d+)"
            )

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")

                matches_section = pattern_section.findall(text)
                if matches_section:
                    last_section = matches_section[0]

                matches_details = pattern_details.findall(text)
                for match in matches_details:
                    extracted_data.append({
                        "name_of_deductor": match[1].strip(),
                        "tan": match[2].strip(),
                        "gross_receipts": match[3].replace(',', ''),
                        "tds_or_tcs_amount": match[4].replace(',', ''),
                        "section": last_section,
                    })

            return extracted_data

        except Exception as e:
            print(f"Error extracting data from PDF: {e}")
            return []


class ChallanPdfUploadSerializer(BaseSerializer):
    challan_pdf = serializers.FileField()

    def extract_challan_details_from_pdf(self, pdf_file):
        try:
            pdf_file.seek(0)
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text")

            pattern_bsr_code = re.compile(r"BSR code\s*:\s*(\d+)")
            pattern_challan_no = re.compile(r"Challan No\s*:\s*(\d+)")
            pattern_date_of_deposit = re.compile(r"Date of Deposit\s*:\s*(\d{2}-[A-Za-z]{3}-\d{4})")
            pattern_amount = re.compile(r"Amount \(in Rs\.\)\s*:\s*₹\s*([\d,]+)")

            bsr_code = pattern_bsr_code.search(text)
            challan_no = pattern_challan_no.search(text)
            date_of_deposit = pattern_date_of_deposit.search(text)
            amount = pattern_amount.search(text)

            if bsr_code and challan_no and date_of_deposit and amount:
                extracted_data = {
                    "bsr_code": bsr_code.group(1),
                    "challan_no": challan_no.group(1),
                    "date_of_deposit": datetime.strptime(date_of_deposit.group(1), "%d-%b-%Y").date(),
                    "amount": amount.group(1).replace(',', '')
                }
                return extracted_data
            else:
                raise serializers.ValidationError("Failed to extract all required data from the PDF.")
        except Exception as e:
            print(f"Error extracting data from PDF: {e}")
            raise serializers.ValidationError("Failed to extract data from PDF.")

    def save_extracted_data(self, extracted_data, income_tax_return, challan_pdf):
        income_tax_profile = income_tax_return.user.income_tax_profile
        saved_record = SelfAssesmentAndAdvanceTaxPaid.objects.create(
            income_tax=income_tax_profile,
            income_tax_return=income_tax_return,
            bsr_code=extracted_data["bsr_code"],
            challan_no=extracted_data["challan_no"],
            date=extracted_data["date_of_deposit"],
            amount=extracted_data["amount"],
            challan_pdf=challan_pdf
        )
        response_data = {
            "id": AlphaId.encode(saved_record.id),
            "bsr_code": saved_record.bsr_code,
            "challan_no": saved_record.challan_no,
            "date_of_deposit": saved_record.date.strftime("%d-%b-%Y"),
            "amount": saved_record.amount,
        }
        return response_data

    def update_extracted_data(self, instance, extracted_data, challan_pdf):
        instance.bsr_code = extracted_data["bsr_code"]
        instance.challan_no = extracted_data["challan_no"]
        instance.date = extracted_data["date_of_deposit"]
        instance.amount = extracted_data["amount"]
        instance.challan_pdf = challan_pdf
        instance.save()

        response_data = {
            "id": AlphaId.encode(instance.id),
            "bsr_code": instance.bsr_code,
            "challan_no": instance.challan_no,
            "date_of_deposit": instance.date.strftime("%d-%b-%Y"),
            "amount": instance.amount,
        }
        return response_data

    def create(self, validated_data):
        challan_pdf = validated_data.get('challan_pdf')
        income_tax_return = self.context.get('income_tax_return')
        extracted_data = self.extract_challan_details_from_pdf(challan_pdf)
        return self.save_extracted_data(extracted_data, income_tax_return, challan_pdf)

    def update(self, instance, validated_data):
        challan_pdf = validated_data.get('challan_pdf')
        extracted_data = self.extract_challan_details_from_pdf(challan_pdf)
        return self.update_extracted_data(instance, extracted_data, challan_pdf)


class ReportsPageGraphDataSerializer(BaseModelSerializer):
    total_income_earned = serializers.SerializerMethodField()
    total_tax_paid = serializers.SerializerMethodField()
    income_tax_return_year_name = serializers.CharField(source='income_tax_return_year.name')

    class Meta:
        model = IncomeTaxReturn
        fields = ['income_tax_return_year_name', 'total_income_earned', 'total_tax_paid']

    def get_total_income_earned(self, obj):
        total_salary_income = SalaryIncome.objects.filter(income_tax_return=obj).aggregate(total=Sum('gross_salary'))['total'] or 0
        total_rental_income = RentalIncome.objects.filter(income_tax_return=obj).aggregate(total=Sum('net_rental_income'))['total'] or 0
        total_capital_gains = CapitalGains.objects.filter(income_tax_return=obj).aggregate(total=Sum('gain_or_loss'))['total'] or 0
        total_business_income = BusinessIncome.objects.filter(income_tax_return=obj).aggregate(total=Sum('gross_receipt_cheq_neft_rtgs_profit') + Sum('gross_receipt_cash_upi_profit'))['total'] or 0
        total_agriculture_income = AgricultureIncome.objects.filter(income_tax_return=obj).aggregate(total=Sum('gross_recipts'))['total'] or 0
        total_exempt_income = ExemptIncome.objects.filter(income_tax_return=obj).aggregate(total=Sum('amount'))['total'] or 0
        total_income = (total_salary_income + total_rental_income + total_capital_gains +
                        total_business_income + total_agriculture_income + total_exempt_income)
        return total_income

    def get_total_tax_paid(self, obj):
        total_tds_or_tcs_amount = TdsOrTcsDeduction.objects.filter(income_tax_return=obj).aggregate(total=Sum('tds_or_tcs_amount'))['total'] or 0
        total_self_assessment_amount = SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax_return=obj).aggregate(total=Sum('amount'))['total'] or 0
        total_taxes_paid = total_tds_or_tcs_amount + total_self_assessment_amount
        return total_taxes_paid


class ReportsPageSerializer(BaseModelSerializer):
    total_income_earned = serializers.SerializerMethodField()
    total_tax_paid = serializers.SerializerMethodField()
    is_pan_verified = serializers.BooleanField(source='user.income_tax_profile.is_pan_verified')
    income_tax_return_year_name = serializers.CharField(source='income_tax_return_year.name')
    ais_pdf_url = serializers.FileField(source='ais_pdf')
    tds_pdf_url = serializers.FileField(source='tds_pdf')
    tis_pdf_url = serializers.FileField(source='tis_pdf')
    income_tax_return_status = serializers.CharField(source='get_status_display')
    contribution_percentage = serializers.SerializerMethodField()

    class Meta:
        model = IncomeTaxReturn
        fields = [
            'income_tax_return_year_name', 'total_income_earned', 'total_tax_paid', 'is_pan_verified',
            'income_tax_return_status', 'ais_pdf_url', 'tds_pdf_url', 'tis_pdf_url', 'contribution_percentage'
        ]

    def get_total_income_earned(self, obj):
        return ReportsPageGraphDataSerializer().get_total_income_earned(obj)

    def get_total_tax_paid(self, obj):
        return ReportsPageGraphDataSerializer().get_total_tax_paid(obj)

    def get_contribution_percentage(self, obj):
        total_income = self.get_total_income_earned(obj)
        total_taxes_paid = self.get_total_tax_paid(obj)
        if total_income == 0:
            return 0
        contribution_percentage = (total_taxes_paid / total_income) * 100
        return round(contribution_percentage, 2)


class TaxSummarySerializer(BaseModelSerializer):
    old_regime = serializers.SerializerMethodField()
    new_regime = serializers.SerializerMethodField()

    class Meta:
        model = IncomeTaxReturn
        fields = ['old_regime', 'new_regime']

    def get_old_regime(self, obj):
        old_income_tax_return = self.get_previous_year_return(obj)
        if old_income_tax_return:
            return self.calculate_tax_summary(old_income_tax_return)
        else:
            return self.get_empty_old_regime_data()

    def get_new_regime(self, obj):
        return self.calculate_tax_summary(obj)

    def get_previous_year_return(self, current_income_tax_return):
        """Retrieve the previous year's income tax return."""
        previous_year = current_income_tax_return.income_tax_return_year.start_date.year - 1
        return IncomeTaxReturn.objects.filter(
            user=current_income_tax_return.user,
            income_tax_return_year__start_date__year=previous_year
        ).first()

    def get_empty_old_regime_data(self):
        return {
            'income_sources': {
                'salary_income': 0,
                'rental_income': 0,
                'capital_gains': 0,
                'business_income': 0,
                'agriculture_and_exempt_income': 0,
                'other_income': 0
            },
            'gross_total_income': 0,
            'deductions': 0,
            'total_income': 0,
            'tax_on_total_income': 0,
            'interest_and_penalties': 0,
            'taxes_paid': 0,
            'tax_payable_or_refund': 0
        }

    def calculate_tax_summary(self, income_tax_return):
        total_salary_income = SalaryIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gross_salary'))['total'] or 0
        total_rental_income = RentalIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('net_rental_income'))['total'] or 0
        total_capital_gains = CapitalGains.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gain_or_loss'))['total'] or 0
        total_business_income = BusinessIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gross_receipt_cheq_neft_rtgs_profit') + Sum('gross_receipt_cash_upi_profit'))['total'] or 0
        total_agriculture_income = AgricultureIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gross_recipts'))['total'] or 0
        total_exempt_income = ExemptIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_interest_income = InterestIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('interest_amount'))['total'] or 0
        total_it_refunds = InterestOnItRefunds.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_dividend_income = DividendIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_betting_income = IncomeFromBetting.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0

        total_others_income = total_interest_income + total_it_refunds + total_dividend_income + total_betting_income

        gross_total_income = (total_salary_income + total_rental_income + total_capital_gains +
                              total_business_income + total_agriculture_income + total_exempt_income + total_others_income)

        deductions = Deductions.objects.filter(income_tax_return=income_tax_return).first()
        total_deductions = (
            deductions.life_insurance + deductions.provident_fund + deductions.elss_mutual_fund +
            deductions.home_loan_repayment + deductions.tution_fees + deductions.stamp_duty_paid +
            deductions.others + deductions.contribution_by_self + deductions.contribution_by_employeer +
            deductions.medical_insurance_self + deductions.medical_preventive_health_checkup_self +
            deductions.medical_expenditure_self + deductions.medical_insurance_parents +
            deductions.medical_preventive_health_checkup_parents + deductions.medical_expenditure_parents +
            deductions.education_loan + deductions.electronic_vehicle_loan + deductions.home_loan_amount +
            deductions.interest_income + deductions.royality_on_books + deductions.income_on_patients +
            deductions.income_on_bio_degradable + deductions.rent_paid + deductions.contribution_to_agnipath +
            deductions.donation_to_political_parties + deductions.donation_others
        ) if deductions else 0

        total_income = gross_total_income - total_deductions
        total_tds_or_tcs_amount = TdsOrTcsDeduction.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('tds_or_tcs_amount'))['total'] or 0
        total_self_assessment_amount = SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_taxes_paid = total_tds_or_tcs_amount + total_self_assessment_amount
        tax_on_total_income = self.calculate_tax_on_total_income(total_income)
        interest_and_penalties = self.calculate_interest_and_penalties(total_income)
        tax_payable_or_refund = total_income - tax_on_total_income - interest_and_penalties - total_taxes_paid

        return {
            'income_sources': {
                'salary_income': total_salary_income,
                'rental_income': total_rental_income,
                'capital_gains': total_capital_gains,
                'business_income': total_business_income,
                'agriculture_and_exempt_income': total_agriculture_income,
                'other_income': total_others_income
            },
            'gross_total_income': gross_total_income,
            'deductions': total_deductions,
            'total_income': total_income,
            'tax_on_total_income': tax_on_total_income,
            'interest_and_penalties': interest_and_penalties,
            'taxes_paid': total_taxes_paid,
            'tax_payable_or_refund': tax_payable_or_refund
        }

    def calculate_tax_on_total_income(self, total_income):
        return 0

    def calculate_interest_and_penalties(self, total_income):
        return 0


class ComputationsSerializer(BaseModelSerializer):
    regime_type = serializers.IntegerField(write_only=True)
    income_tax_return_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Computations
        fields = ['income_tax_return_id', 'regime_type', 'regime_json_data']

    def to_internal_value(self, data):
        regime_type_str = data.get('regime_type', '').lower()
        if regime_type_str == 'new':
            data['regime_type'] = Computations.New
        elif regime_type_str == 'old':
            data['regime_type'] = Computations.Old
        else:
            raise serializers.ValidationError({'regime_type': 'Invalid regime type. Use "new" or "old".'})
        return super().to_internal_value(data)

    def validate(self, data):
        income_tax_return = self.context.get('income_tax_return')
        regime_type = data.get('regime_type')

        if Computations.objects.filter(
                income_tax_return=income_tax_return,
                regime_type=regime_type
        ).exists():
            raise serializers.ValidationError({
                'regime_type': f'This income tax return already has a {self.get_regime_type_display()} regime.'
            })

        return data

    def create(self, validated_data):
        income_tax_return = validated_data.pop('income_tax_return', None)
        computation = Computations.objects.create(
            income_tax_return=income_tax_return,
            **validated_data
        )
        return computation

    def update(self, instance, validated_data):
        instance.regime_type = validated_data.get('regime_type', instance.regime_type)
        instance.regime_json_data = validated_data.get('regime_json_data', instance.regime_json_data)
        instance.save()
        return instance