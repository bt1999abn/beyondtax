import re
from datetime import datetime
import fitz
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
        extra_kwargs = {'capital_gains': {'required': False}}


class CapitalGainsSerializer(serializers.ModelSerializer):
    buyer_details = BuyerDetailsSerializer(many=True, required=False)

    class Meta:
        model = CapitalGains
        fields = "__all__"

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

        # Update or create buyer details
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


class AgricultureAndExemptIncomeSerializer(serializers.Serializer):
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


class OtherIncomesSerializer(serializers.Serializer):
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


class TaxPaidSerializer(serializers.Serializer):
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


class AISPdfUploadSerializer(serializers.Serializer):
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


class TdsPdfSerializer(serializers.Serializer):
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


class ChallanPdfUploadSerializer(serializers.Serializer):
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
            "id": saved_record.id,
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
            "id": instance.id,
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