import json
from io import BytesIO
from decimal import Decimal
from urllib.parse import unquote
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from xhtml2pdf import pisa

from services.incomeTax.models import IncomeTaxProfile, IncomeTaxReturn, IncomeTaxReturnYears, \
    ResidentialStatusQuestions, IncomeTaxBankDetails, IncomeTaxAddress, SalaryIncome, RentalIncome, BuyerDetails, \
    CapitalGains, BusinessIncome, AgricultureIncome, LandDetails, InterestIncome, InterestOnItRefunds, DividendIncome, \
    IncomeFromBetting, TdsOrTcsDeduction, SelfAssesmentAndAdvanceTaxPaid, Deductions, ExemptIncome, Computations
from services.incomeTax.serializers import IncomeTaxReturnSerializer, ResidentialStatusQuestionsSerializer, \
    SalaryIncomeSerializer, RentalIncomeSerializer, \
    CapitalGainsSerializer, BusinessIncomeSerializer, AgricultureIncomeSerializer, InterestIncomeSerializer, \
    InterestOnItRefundsSerializer, DividendIncomeSerializer, IncomeFromBettingSerializer, TdsOrTcsDeductionSerializer, \
    SelfAssesmentAndAdvanceTaxPaidSerializer, DeductionsSerializer, ExemptIncomeSerializer, BuyerDetailsSerializer, \
    LandDetailsSerializer, AgricultureAndExemptIncomeSerializer, OtherIncomesSerializer, TaxPaidSerializer, \
    TdsPdfSerializer, ChallanPdfUploadSerializer, AISPdfUploadSerializer, IncomeTaxReturnYearSerializer, \
    ReportsPageSerializer, ReportsPageGraphDataSerializer, TaxSummarySerializer, ComputationsSerializer, \
    IncomeTaxProfileSerializer
from services.incomeTax.services import PanVerificationService
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from services.incomeTax.utils import IncomeTaxCurrentYear, IncomeTaxCalculations
from shared.libs.hashing import AlphaId


class IncomeTaxProfileApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            profile = IncomeTaxProfile.objects.get(user=user)
            profile_serializer = IncomeTaxProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        except IncomeTaxProfile.DoesNotExist:
            profile_serializer = IncomeTaxProfileSerializer(data=request.data, context={'request': request})

        if profile_serializer.is_valid():
            profile = profile_serializer.save()
            return Response(IncomeTaxProfileSerializer(profile, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            profile = IncomeTaxProfile.objects.get(user=request.user)
        except IncomeTaxProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = IncomeTaxProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(IncomeTaxProfileSerializer(profile).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            profile = IncomeTaxProfile.objects.get(user=request.user)
        except IncomeTaxProfile.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

        serializer = IncomeTaxProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListIncomeTaxReturnsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        income_tax_returns = IncomeTaxReturn.objects.filter(user=user).order_by(
            '-income_tax_return_year__start_date')
        serializer = IncomeTaxReturnSerializer(income_tax_returns, many=True)
        income_tax_profile = IncomeTaxProfile.objects.filter(user=user).first()
        is_pan_verified = income_tax_profile.is_pan_verified if income_tax_profile else False
        is_data_imported = income_tax_profile.is_data_imported if income_tax_profile else False
        response_data = [
            {
                'id': record['id'],
                'name': record['income_tax_return_year']['name'],
                'status': record['status_display']
            }
            for record in serializer.data
        ]
        return Response({
            'status_code': 200,
            'status_text': 'OK',
            'data': response_data,
            'is_pan_verified': is_pan_verified,
            'is_data_imported': is_data_imported
        })


class ResidentialStatusQuestionsListView(APIView):
    def get(self, request, format=None):
        questions = ResidentialStatusQuestions.objects.all()
        serializer = ResidentialStatusQuestionsSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SendPanVerificationOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            tax_profile = IncomeTaxProfile.objects.get(user=user)
            pan_number = tax_profile.pan_no
        except IncomeTaxProfile.DoesNotExist:
            pan_number = request.data.get('pan_number')
            if not pan_number:
                return Response({'status': 'error', 'message': 'PAN number is required for new users'},
                                status=status.HTTP_400_BAD_REQUEST)
        if not user.email:
            return Response({'status': 'error', 'message': 'No email associated with this user'},
                            status=status.HTTP_400_BAD_REQUEST)
        pan_service = PanVerificationService()
        otp_id = pan_service.send_pan_verification_otp(user, pan_number)
        return Response({'status': 'success', 'message': 'OTP sent to your email', 'otp_id': otp_id},
                        status=status.HTTP_200_OK)


class VerifyPanOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        otp_id = request.data.get('otp_id')
        otp = request.data.get('otp')
        new_pan_number = request.data.get('new_pan_number')

        if not otp:
            return Response({'status': 'error', 'message': 'OTP is a required field'},
                            status=status.HTTP_400_BAD_REQUEST)
        otp_id_decoded = AlphaId.decode(otp_id)
        pan_service = PanVerificationService()
        if pan_service.verify_pan_otp(otp_id_decoded, otp):
            user = request.user
            try:
                income_tax_profile = IncomeTaxProfile.objects.get(user=user)
            except IncomeTaxProfile.DoesNotExist:
                if not new_pan_number:
                    return Response({'status': 'error', 'message': 'No PAN number provided for new user.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if IncomeTaxProfile.objects.filter(pan_no=new_pan_number).exists():
                    return Response({'status': 'error', 'message': 'This PAN number is already in use'},
                                    status=status.HTTP_400_BAD_REQUEST)
                IncomeTaxReturn.objects.filter(user=user).delete()
                income_tax_profile = IncomeTaxProfile.objects.create(
                    user=user,
                    pan_no=new_pan_number,
                    is_pan_verified=True
                )

            income_tax_profile.is_pan_verified = True
            income_tax_profile.save()
            income_tax_return_years = IncomeTaxReturnYears.objects.filter(status=IncomeTaxReturnYears.Open)
            created_records = []
            for year in income_tax_return_years:
                tax_return = IncomeTaxReturn.objects.create(
                    user=user,
                    income_tax_return_year=year,
                    status=IncomeTaxReturn.NotFiled
                )
                created_records.append({
                    'status': tax_return.get_status_display(),
                    'name': year.name,
                    'year_id': AlphaId.encode(year.id)
                })
            return Response({
                'status_code': 200,
                'status_text': 'OK',
                'data': {
                    'status': 'success',
                    'message': 'PAN OTP verification successful',
                    'is_pan_verified': income_tax_profile.is_pan_verified,
                    'pan_number': income_tax_profile.pan_no,
                    'income_tax_returns': created_records
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'message': 'Invalid or expired OTP'},
                            status=status.HTTP_400_BAD_REQUEST)


class ImportIncomeTaxProfileDataApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        email = user.email or ''
        date_of_birth = user.date_of_birth or None

        try:
            income_tax_profile = IncomeTaxProfile.objects.get(user=user)
            pan_no = income_tax_profile.pan_no
        except IncomeTaxProfile.DoesNotExist:
            return Response({'status': 'error', 'message': 'Income Tax Profile does not exist for the user'},
                            status=status.HTTP_404_NOT_FOUND)

        income_tax_profile, created = IncomeTaxProfile.objects.update_or_create(
            user=user,
            defaults={
                'first_name': first_name,
                'middle_name': '',
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'fathers_name': 'Father Beyondtax',
                'gender': IncomeTaxProfile.MALE,
                'marital_status': IncomeTaxProfile.Married,
                'aadhar_no': '123456789012',
                'aadhar_enrollment_no': '123456789012345678901234',
                'pan_no': pan_no,
                'mobile_number': '',
                'email': email,
                'residential_status': IncomeTaxProfile.IndianResident,
                'is_data_imported': True
            }
        )
        IncomeTaxBankDetails.objects.update_or_create(
            income_tax=income_tax_profile,
            defaults={
                'account_no': '',
                'ifsc_code': '',
                'bank_name': '',
                'type': IncomeTaxBankDetails.SavingsAccount
            }
        )

        IncomeTaxAddress.objects.update_or_create(
            income_tax=income_tax_profile,
            defaults={
                'door_no': '',
                'permise_name': '',
                'street': '',
                'area': '',
                'city': '',
                'state': '',
                'pincode': '',
                'country': ''
            }
        )

        message = 'Tax profile data created successfully' if created else 'Tax profile data updated successfully'
        return Response({'status': 'success', 'message': message, 'is_data_imported': True},
                        status=status.HTTP_201_CREATED)


class SalaryIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SalaryIncomeSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        return SalaryIncome.objects.filter(income_tax__user=user,
                                               income_tax_return_id=income_tax_return_id)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data.getlist('data')
        files = request.FILES.getlist('files')
        if isinstance(data, list):
            created_incomes = []
            for item_data, file in zip(data, files):
                item = eval(item_data)
                item['income_tax'] = AlphaId.encode(income_tax_profile.id)
                item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
                item['upload_form_file'] = file
                serializer = self.get_serializer(data=item)
                serializer.is_valid(raise_exception=True)
                salary_income = serializer.save()
                created_incomes.append(serializer.data)
            return Response(
                {'status': 'success', 'message': 'Salary incomes created successfully', 'data': created_incomes},
                status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of salary incomes'},
                            status=status.HTTP_400_BAD_REQUEST)


class SalaryIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SalaryIncomeSerializer
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)

        data = request.data.getlist('data')
        files = request.FILES.getlist('files')

        if isinstance(data, list):
            updated_ids = []
            for item_data, file in zip(data, files):
                try:
                    item_dict = json.loads(item_data)
                except json.JSONDecodeError as e:
                    return Response(
                        {'status': 'failure', 'message': 'Invalid JSON format in data'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                item_dict['income_tax'] = income_tax_profile
                item_dict['income_tax_return'] = income_tax_return
                item_dict['upload_form_file'] = file
                if 'id' in item_dict:
                    item_dict['id'] = AlphaId.decode(item_dict['id'])
                salary_income, created = SalaryIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item_dict.get('id'),
                    defaults=item_dict
                )
                updated_ids.append(salary_income.id)

            SalaryIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
                id__in=updated_ids).delete()

            return Response({'status': 'success', 'message': 'Salary incomes updated successfully'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of salary incomes'},
                            status=status.HTTP_400_BAD_REQUEST)


class RentalIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentalIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        return RentalIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            created_incomes = []
            for item in data:
                item['income_tax'] = AlphaId.encode(income_tax_profile.id)
                item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
                serializer = self.get_serializer(data=item)
                serializer.is_valid(raise_exception=True)
                rental_income = serializer.save()
                created_incomes.append(serializer.data)

            return Response({'status': 'success', 'message': 'Rental incomes created successfully', 'data': created_incomes}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of rental incomes'}, status=status.HTTP_400_BAD_REQUEST)


class RentalIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentalIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                if 'id' in item:
                    item['id'] = AlphaId.decode(item['id'])

                rental_income, created = RentalIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(rental_income.id)
            RentalIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
                id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Rental incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of rental incomes'}, status=status.HTTP_400_BAD_REQUEST)


class CapitalGainsListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CapitalGainsSerializer

    def get_queryset(self):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        return CapitalGains.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data

        if isinstance(data, dict):
            data = [data]
        created_records = []
        for item in data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            asset_type = item.get('asset_type')
            term_type = item.get('term_type', None)
            if asset_type == CapitalGains.HouseProperty:
                irrelevant_fields = ['stt_paid', 'isn_code', 'fund_date', 'fair_value_per_unit', 'sale_price_per_unit', 'purchase_price_per_unit', 'no_of_units']
            elif asset_type == CapitalGains.ListedSharesOrMutualFunds:
                irrelevant_fields = ['property_door_no', 'property_city', 'property_area', 'property_pin', 'property_state', 'property_country']
                if term_type == CapitalGains.ShortTerm:
                    item.pop('isn_code', None)
                    item.pop('fair_value_per_unit', None)
                elif term_type == CapitalGains.LongTerm:
                    item.pop('no_of_units', None)
            else:
                irrelevant_fields = []
            for field in irrelevant_fields:
                item.pop(field, None)
            serializer = self.get_serializer(data=item)
            serializer.is_valid(raise_exception=True)
            capital_gain = serializer.save()
            created_records.append(serializer.data)
            buyers_data = item.get('buyer_details', [])
            for buyer in buyers_data:
                buyer['capital_gains'] = AlphaId.encode(capital_gain.id)
                buyer_serializer = BuyerDetailsSerializer(data=buyer)
                buyer_serializer.is_valid(raise_exception=True)
                buyer_serializer.save()
            updated_data = self.get_serializer(capital_gain).data
            created_records[-1] = updated_data
        return Response({'status': 'success', 'message': 'Capital gains created successfully', 'data': created_records}, status=status.HTTP_201_CREATED)


class CapitalGainsUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CapitalGainsSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data

        if isinstance(data, dict):
            data = [data]
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                buyers_data = item.pop('buyer_details', [])
                if 'id' in item:
                    item['id'] = AlphaId.decode(item['id'])

                capital_gain, created = CapitalGains.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(capital_gain.id)

                buyer_ids = []
                for buyer in buyers_data:
                    if 'id' in buyer:
                        buyer['id'] = AlphaId.decode(buyer['id'])
                    buyer['capital_gains'] = capital_gain

                    buyer_detail, created = BuyerDetails.objects.update_or_create(
                        id=buyer.get('id'),
                        defaults=buyer
                    )
                    buyer_ids.append(buyer_detail.id)

                BuyerDetails.objects.filter(capital_gains=capital_gain).exclude(id__in=buyer_ids).delete()

            CapitalGains.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
                id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Capital gains and buyer details updated successfully'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of capital gains'},
                            status=status.HTTP_400_BAD_REQUEST)


class BusinessIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        return BusinessIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        created_records = []
        for item in data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            serializer = self.get_serializer(data=item)
            serializer.is_valid(raise_exception=True)
            record = serializer.save()
            created_records.append(serializer.data)
        return Response({'status': 'success', 'message': 'Business incomes created successfully', 'data': created_records}, status=status.HTTP_201_CREATED)


class BusinessIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                if 'id' in item:
                    item['id'] = AlphaId.decode(item['id'])

                business_income, created = BusinessIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(business_income.id)
            BusinessIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
                id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Business incomes updated successfully'},
                            status=status.HTTP_200_OK)
        else:
            return Response(
                {'status': 'failure', 'message': 'Invalid data format, expected a list of business incomes'},
                status=status.HTTP_400_BAD_REQUEST)


class AgricultureAndExemptIncomeApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AgricultureAndExemptIncomeSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)

        agriculture_incomes = AgricultureIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        exempt_incomes = ExemptIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)

        data = {
            'agriculture_incomes': AgricultureIncomeSerializer(agriculture_incomes, many=True).data,
            'exempt_incomes': ExemptIncomeSerializer(exempt_incomes, many=True).data
        }
        return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data

        created_records = {}
        agriculture_incomes_data = data.get('agriculture_incomes', [])
        agriculture_incomes_created = []
        for item in agriculture_incomes_data:
            land_data = item.pop('land_details', [])
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item.pop('id', None)

            agriculture_serializer = AgricultureIncomeSerializer(data=item)
            agriculture_serializer.is_valid(raise_exception=True)
            agriculture_income = agriculture_serializer.save()
            agriculture_incomes_created.append(agriculture_serializer.data)

            for land in land_data:
                land['agriculture_income'] = AlphaId.encode(agriculture_income.id)
                land.pop('id', None)
                land_serializer = LandDetailsSerializer(data=land)
                land_serializer.is_valid(raise_exception=True)
                land_serializer.save()
            updated_data = AgricultureIncomeSerializer(agriculture_income).data
            agriculture_incomes_created[-1] = updated_data

        created_records['agriculture_incomes'] = agriculture_incomes_created
        exempt_incomes_data = data.get('exempt_incomes', [])
        exempt_incomes_created = []
        for item in exempt_incomes_data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item.pop('id', None)
            exempt_serializer = ExemptIncomeSerializer(data=item)
            exempt_serializer.is_valid(raise_exception=True)
            exempt_income = exempt_serializer.save()
            exempt_incomes_created.append(exempt_serializer.data)
        created_records['exempt_incomes'] = exempt_incomes_created
        return Response({'status': 'success', 'message': 'Agriculture And Exempt Incomes created successfully', 'data': created_records}, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data

        updated_records = {}
        agriculture_incomes_data = data.get('agriculture_incomes', [])
        agriculture_incomes_updated = []
        for item in agriculture_incomes_data:
            land_data = item.pop('land_details', [])
            item['id'] = AlphaId.decode(item.get('id'))
            agriculture_income, created = AgricultureIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            land_ids = []
            for land in land_data:
                land['id'] = AlphaId.decode(land.get('id'))
                land_detail, land_created = LandDetails.objects.update_or_create(
                    agriculture_income=agriculture_income,
                    id=land.get('id'),
                    defaults=land
                )
                land_ids.append(land_detail.id)
            LandDetails.objects.filter(agriculture_income=agriculture_income).exclude(id__in=land_ids).delete()
            agriculture_incomes_updated.append(AgricultureIncomeSerializer(agriculture_income).data)

        updated_records['agriculture_incomes'] = agriculture_incomes_updated
        exempt_incomes_data = data.get('exempt_incomes', [])
        exempt_incomes_updated = []
        for item in exempt_incomes_data:
            item['id'] = AlphaId.decode(item.get('id'))
            exempt_income, created = ExemptIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            exempt_incomes_updated.append(ExemptIncomeSerializer(exempt_income).data)
        updated_records['exempt_incomes'] = exempt_incomes_updated
        return Response({'status': 'success', 'message': 'Incomes updated successfully', 'data': updated_records}, status=status.HTTP_200_OK)


class OtherIncomesApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OtherIncomesSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        interest_incomes = InterestIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        interest_on_it_refunds = InterestOnItRefunds.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        dividend_incomes = DividendIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        income_from_betting = IncomeFromBetting.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        data = {
            'interest_incomes': InterestIncomeSerializer(interest_incomes, many=True).data,
            'interest_on_it_refunds': InterestOnItRefundsSerializer(interest_on_it_refunds, many=True).data,
            'dividend_incomes': DividendIncomeSerializer(dividend_incomes, many=True).data,
            'income_from_betting': IncomeFromBettingSerializer(income_from_betting, many=True).data,
        }
        return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data

        created_records = {}
        interest_incomes_data = data.get('interest_incomes', [])
        interest_incomes_created = []
        for item in interest_incomes_data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item.pop('id', None)

            interest_serializer = InterestIncomeSerializer(data=item)
            interest_serializer.is_valid(raise_exception=True)
            interest_income = interest_serializer.save()
            interest_incomes_created.append(interest_serializer.data)

        created_records['interest_incomes'] = interest_incomes_created
        interest_on_it_refunds_data = data.get('interest_on_it_refunds', [])
        interest_on_it_refunds_created = []
        for item in interest_on_it_refunds_data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item.pop('id', None)

            interest_on_it_refunds_serializer = InterestOnItRefundsSerializer(data=item)
            interest_on_it_refunds_serializer.is_valid(raise_exception=True)
            interest_on_it_refund = interest_on_it_refunds_serializer.save()
            interest_on_it_refunds_created.append(interest_on_it_refunds_serializer.data)

        created_records['interest_on_it_refunds'] = interest_on_it_refunds_created
        dividend_incomes_data = data.get('dividend_incomes', [])
        dividend_incomes_created = []
        for item in dividend_incomes_data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item.pop('id', None)

            dividend_serializer = DividendIncomeSerializer(data=item)
            dividend_serializer.is_valid(raise_exception=True)
            dividend_income = dividend_serializer.save()
            dividend_incomes_created.append(dividend_serializer.data)

        created_records['dividend_incomes'] = dividend_incomes_created
        income_from_betting_data = data.get('income_from_betting', [])
        income_from_betting_created = []
        for item in income_from_betting_data:
            item['income_tax'] = AlphaId.encode(income_tax_profile.id)
            item['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item.pop('id', None)

            betting_serializer = IncomeFromBettingSerializer(data=item)
            betting_serializer.is_valid(raise_exception=True)
            income_from_betting = betting_serializer.save()
            income_from_betting_created.append(betting_serializer.data)

        created_records['income_from_betting'] = income_from_betting_created

        return Response({'status': 'success', 'message': 'Incomes created successfully', 'data': created_records}, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = get_object_or_404(IncomeTaxProfile, user=user)
        income_tax_return = get_object_or_404(IncomeTaxReturn, id=income_tax_return_id, user=user)
        data = request.data

        updated_records = {}

        interest_incomes_data = data.get('interest_incomes', [])
        interest_ids = [AlphaId.decode(item.get('id')) if 'id' in item else None for item in interest_incomes_data]
        InterestIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
            id__in=interest_ids).delete()
        interest_incomes_updated = []
        for item in interest_incomes_data:
            if 'id' in item:
                item['id'] = AlphaId.decode(item['id'])
            interest_income, created = InterestIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            interest_incomes_updated.append(InterestIncomeSerializer(interest_income).data)
        updated_records['interest_incomes'] = interest_incomes_updated

        interest_on_it_refunds_data = data.get('interest_on_it_refunds', [])
        it_refund_ids = [AlphaId.decode(item.get('id')) if 'id' in item else None for item in
                         interest_on_it_refunds_data]
        InterestOnItRefunds.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
            id__in=it_refund_ids).delete()
        interest_on_it_refunds_updated = []
        for item in interest_on_it_refunds_data:
            if 'id' in item:
                item['id'] = AlphaId.decode(item['id'])
            interest_on_it_refund, created = InterestOnItRefunds.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            interest_on_it_refunds_updated.append(InterestOnItRefundsSerializer(interest_on_it_refund).data)
        updated_records['interest_on_it_refunds'] = interest_on_it_refunds_updated

        dividend_incomes_data = data.get('dividend_incomes', [])
        dividend_ids = [AlphaId.decode(item.get('id')) if 'id' in item else None for item in dividend_incomes_data]
        DividendIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
            id__in=dividend_ids).delete()
        dividend_incomes_updated = []
        for item in dividend_incomes_data:
            if 'id' in item:
                item['id'] = AlphaId.decode(item['id'])
            dividend_income, created = DividendIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            dividend_incomes_updated.append(DividendIncomeSerializer(dividend_income).data)
        updated_records['dividend_incomes'] = dividend_incomes_updated

        income_from_betting_data = data.get('income_from_betting', [])
        betting_ids = [AlphaId.decode(item.get('id')) if 'id' in item else None for item in income_from_betting_data]
        IncomeFromBetting.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
            id__in=betting_ids).delete()
        income_from_betting_updated = []
        for item in income_from_betting_data:
            if 'id' in item:
                item['id'] = AlphaId.decode(item['id'])
            income_from_betting, created = IncomeFromBetting.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            income_from_betting_updated.append(IncomeFromBettingSerializer(income_from_betting).data)
        updated_records['income_from_betting'] = income_from_betting_updated

        return Response({'status': 'success', 'message': 'Incomes updated successfully', 'data': updated_records},
                        status=status.HTTP_200_OK)


class TaxPaidApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxPaidSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)

        tds_or_tcs_deductions = TdsOrTcsDeduction.objects.filter(income_tax=income_tax_profile,
                                                                 income_tax_return=income_tax_return)
        self_assessment_and_advance_tax_paid = SelfAssesmentAndAdvanceTaxPaid.objects.filter(
            income_tax=income_tax_profile, income_tax_return=income_tax_return)

        data = {
            'tds_or_tcs_deductions': TdsOrTcsDeductionSerializer(tds_or_tcs_deductions, many=True).data,
            'self_assessment_and_advance_tax_paid': SelfAssesmentAndAdvanceTaxPaidSerializer(
                self_assessment_and_advance_tax_paid, many=True).data,
        }

        return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)

        tds_data = request.data.getlist('tds_or_tcs_deductions')
        self_assessment_data = request.data.getlist('self_assessment_and_advance_tax_paid')
        files = request.FILES.getlist('files')

        created_tds_records = []
        for item in tds_data:
            item_dict = json.loads(item)
            item_dict['income_tax'] = AlphaId.encode(income_tax_profile.id)  # Assign to item_dict
            item_dict['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            serializer = TdsOrTcsDeductionSerializer(data=item_dict)
            serializer.is_valid(raise_exception=True)
            record = serializer.save()
            created_tds_records.append(serializer.data)

        created_self_assessment_records = []
        for item_data, file in zip(self_assessment_data, files):
            item_data_dict = json.loads(item_data)
            item_data_dict['income_tax'] = AlphaId.encode(income_tax_profile.id)  # Assign to item_data_dict
            item_data_dict['income_tax_return'] = AlphaId.encode(income_tax_return.id)
            item_data_dict['challan_pdf'] = file
            serializer = SelfAssesmentAndAdvanceTaxPaidSerializer(data=item_data_dict)
            serializer.is_valid(raise_exception=True)
            record = serializer.save()
            created_self_assessment_records.append(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Records created successfully',
            'tds_or_tcs_deductions': created_tds_records,
            'self_assessment_and_advance_tax_paid': created_self_assessment_records
        }, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)

        tds_data = request.data.getlist('tds_or_tcs_deductions', [])
        self_assessment_data = request.data.getlist('self_assessment_and_advance_tax_paid', [])
        files = request.FILES.getlist('files')

        updated_tds_ids = []
        for item in tds_data:
            item_dict = json.loads(item)
            if 'id' in item_dict:
                item_dict['id'] = AlphaId.decode(item_dict['id'])
            item_dict['income_tax'] = income_tax_profile
            item_dict['income_tax_return'] = income_tax_return
            tds_or_tcs_deduction, created = TdsOrTcsDeduction.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item_dict.get('id'),
                defaults=item_dict
            )
            updated_tds_ids.append(tds_or_tcs_deduction.id)

        TdsOrTcsDeduction.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(
            id__in=updated_tds_ids).delete()

        updated_self_assessment_ids = []
        for item_data, file in zip(self_assessment_data, files):
            item_data_dict = json.loads(item_data)
            if 'id' in item_data_dict:
                item_data_dict['id'] = AlphaId.decode(item_data_dict['id'])
            item_data_dict['income_tax'] = income_tax_profile
            item_data_dict['income_tax_return'] = income_tax_return
            item_data_dict['challan_pdf'] = file
            self_assessment_and_advance_tax_paid, created = SelfAssesmentAndAdvanceTaxPaid.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item_data_dict.get('id'),
                defaults=item_data_dict
            )
            updated_self_assessment_ids.append(self_assessment_and_advance_tax_paid.id)

        SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax=income_tax_profile,
                                                      income_tax_return=income_tax_return).exclude(
            id__in=updated_self_assessment_ids).delete()

        return Response({
            'status': 'success',
            'message': 'Records updated successfully',
        }, status=status.HTTP_200_OK)


class DeductionsApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeductionsSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        try:
            deductions = Deductions.objects.get(income_tax__user=user, income_tax_return_id=income_tax_return_id)
            serializer = DeductionsSerializer(deductions)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Deductions.DoesNotExist:
            return Response({'status': 'failure', 'message': 'Deductions not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        data['income_tax'] = AlphaId.encode(income_tax_profile.id)
        data['income_tax_return'] = AlphaId.encode(income_tax_return.id)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({'status': 'success', 'message': 'Deductions created successfully', 'data': serializer.data},
                        status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        try:
            deductions = Deductions.objects.get(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        except Deductions.DoesNotExist:
            income_tax_profile = IncomeTaxProfile.objects.get(user=user)
            income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
            deductions = Deductions.objects.create(income_tax=income_tax_profile, income_tax_return=income_tax_return, **request.data)
        serializer = DeductionsSerializer(deductions, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TotalIncomeGetAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        income_tax_profile = get_object_or_404(IncomeTaxProfile, user=user)
        income_tax_return = get_object_or_404(IncomeTaxReturn, id=income_tax_return_id, user=user)

        salary_incomes = SalaryIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_salary_income = salary_incomes.aggregate(total=Sum('gross_salary'))['total'] or 0
        salary_data = [{'employer_name': item.employer_name, 'gross_salary': item.gross_salary} for item in salary_incomes]
        is_salary_income_edited = total_salary_income > 0

        rental_incomes = RentalIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_rental_income = rental_incomes.aggregate(total=Sum('net_rental_income'))['total'] or 0
        rental_data = [{'tenant_name': 'Self-occupied' if item.occupancy_status == RentalIncome.SelfOccupied else item.tenant_name, 'net_rental_income': item.net_rental_income} for item in rental_incomes]
        is_rental_income_edited = total_rental_income > 0

        capital_gains = CapitalGains.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_capital_gains = capital_gains.aggregate(total=Sum('gain_or_loss'))['total'] or 0
        is_capital_gains_edited = total_capital_gains > 0

        business_incomes = BusinessIncome.objects.filter(income_tax=income_tax_profile,income_tax_return=income_tax_return)
        total_business_income = business_incomes.aggregate(
            total=Sum('gross_receipt_cheq_neft_rtgs_profit') + Sum('gross_receipt_cash_upi_profit'))['total'] or 0
        # business_data = [{'business_name': item.business_name,
        #                   'gross_receipt_cheq_neft_rtgs_profit': item.gross_receipt_cheq_neft_rtgs_profit,
        #                   'gross_receipt_cash_upi_profit': item.gross_receipt_cash_upi_profit} for item in
        #                  business_incomes]
        is_business_income_edited = total_business_income > 0

        agriculture_incomes = AgricultureIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_agriculture_income = agriculture_incomes.aggregate(total=Sum('gross_recipts'))['total'] or 0

        exempt_incomes = ExemptIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_exempt_income = exempt_incomes.aggregate(total=Sum('amount'))['total'] or 0

        total_agriculture_and_exempt_income = total_agriculture_income + total_exempt_income
        is_agriculture_and_exempt_income_edited = total_agriculture_and_exempt_income > 0

        interest_incomes = InterestIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_interest_income = interest_incomes.aggregate(total=Sum('interest_amount'))['total'] or 0

        it_refunds = InterestOnItRefunds.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_it_refunds = it_refunds.aggregate(total=Sum('amount'))['total'] or 0

        dividend_incomes = DividendIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_dividend_income = dividend_incomes.aggregate(total=Sum('amount'))['total'] or 0

        betting_incomes = IncomeFromBetting.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return)
        total_betting_income = betting_incomes.aggregate(total=Sum('amount'))['total'] or 0

        total_others_income = total_interest_income + total_it_refunds + total_dividend_income + total_betting_income
        is_others_income_edited = total_others_income > 0

        return Response({
            'total_salary_income': total_salary_income,
            'salary_details': salary_data,
            'is_salary_income_edited': is_salary_income_edited,
            'total_rental_income': total_rental_income,
            'rental_details': rental_data,
            'is_rental_income_edited': is_rental_income_edited,
            'total_capital_gains': total_capital_gains,
            'is_capital_gains_edited': is_capital_gains_edited,
            'total_business_income': total_business_income,
            # 'business_details': business_data,
            'is_business_income_edited': is_business_income_edited,
            'total_agriculture_and_exempt_income': total_agriculture_and_exempt_income,
            'is_agriculture_and_exempt_income_edited': is_agriculture_and_exempt_income_edited,
            'total_others_income': total_others_income,
            'is_others_income_edited': is_others_income_edited,
        })


class TotalSummaryGetAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_return = get_object_or_404(IncomeTaxReturn, id=income_tax_return_id, user=user)
        income_tax_profile = income_tax_return.user.income_tax_profile

        total_salary_income = SalaryIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gross_salary'))['total'] or 0
        total_rental_income = RentalIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('net_rental_income'))['total'] or 0
        total_capital_gains = CapitalGains.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gain_or_loss'))['total'] or 0
        total_agriculture_income = AgricultureIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('gross_recipts'))['total'] or 0
        total_exempt_income = ExemptIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_interest_income = InterestIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('interest_amount'))['total'] or 0
        total_it_refunds = InterestOnItRefunds.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_dividend_income = DividendIncome.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_betting_income = IncomeFromBetting.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_business_income = BusinessIncome.objects.filter(income_tax_return=income_tax_return).aggregate(
            total=Sum('gross_receipt_cheq_neft_rtgs_profit') + Sum('gross_receipt_cash_upi_profit'))['total'] or 0

        total_income = (
            total_salary_income + total_rental_income + total_capital_gains +
            total_agriculture_income + total_exempt_income + total_interest_income +
            total_it_refunds + total_dividend_income + total_betting_income +
            total_business_income
        )

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

        total_tds_or_tcs_amount = TdsOrTcsDeduction.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('tds_or_tcs_amount'))['total'] or 0
        total_self_assessment_amount = SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax_return=income_tax_return).aggregate(total=Sum('amount'))['total'] or 0
        total_taxes_paid = total_tds_or_tcs_amount + total_self_assessment_amount

        return Response({
            'income_tax_return_year': income_tax_return.income_tax_return_year.name,
            'total_income': total_income,
            'total_deductions': total_deductions,
            'total_taxes_paid': total_taxes_paid,
            'total_tax_refund': 0,
        }, status=status.HTTP_200_OK)


class AISPdfUploadApi(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AISPdfUploadSerializer

    def post(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        try:
            income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=request.user)
        except IncomeTaxReturn.DoesNotExist:
            return Response({"error": "IncomeTaxReturn not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.context['income_tax_return'] = income_tax_return
        saved_data = serializer.save()

        response_data = {
            "salary": SalaryIncomeSerializer(saved_data["salary"], many=True).data,
            "rent_received": RentalIncomeSerializer(saved_data["rent_received"], many=True).data,
            "business_receipts": BusinessIncomeSerializer(saved_data["business_receipts"], many=True).data,
            "dividends": DividendIncomeSerializer(saved_data["dividends"], many=True).data,
            "interest_income": InterestIncomeSerializer(saved_data["interest_income"], many=True).data
        }

        return Response({"message": "Data processed successfully", "data": response_data}, status=status.HTTP_200_OK)


class TdsPdfUploadApi(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TdsPdfSerializer

    def create(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        serializer = self.get_serializer(data=request.data, context={'request': request, 'income_tax_return_id': income_tax_return_id})
        serializer.is_valid(raise_exception=True)
        saved_records = serializer.save()
        response_serializer = TdsOrTcsDeductionSerializer(saved_records, many=True)
        return Response({
            "message": "Data processed successfully",
            "data": response_serializer.data
        }, status=status.HTTP_200_OK)


class ChallanUploadApi(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChallanPdfUploadSerializer

    def post(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        try:
            income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=request.user)
        except IncomeTaxReturn.DoesNotExist:
            return Response({"error": "IncomeTaxReturn not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.context['income_tax_return'] = income_tax_return
        saved_data = serializer.save()

        return Response({"message": "Data processed successfully", "data": saved_data}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        encoded_income_tax_return_id = kwargs.get('income_tax_return_id')
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        encoded_challan_id = request.data.get('id')
        challan_id = AlphaId.decode(encoded_challan_id)

        try:
            income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=request.user)
        except IncomeTaxReturn.DoesNotExist:
            return Response({"error": "IncomeTaxReturn not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            challan_instance = SelfAssesmentAndAdvanceTaxPaid.objects.get(id=challan_id, income_tax_return=income_tax_return)
        except SelfAssesmentAndAdvanceTaxPaid.DoesNotExist:
            return Response({"error": "Challan record not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.context['income_tax_return'] = income_tax_return
        updated_data = serializer.update(instance=challan_instance, validated_data=request.data)

        return Response({"message": "Data updated successfully", "data": updated_data}, status=status.HTTP_200_OK)


class ReportsPageAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_year_name = self.kwargs.get('income_tax_return_year_name', None)

        if income_tax_return_year_name:
            income_tax_return_year = get_object_or_404(IncomeTaxReturnYears, name=income_tax_return_year_name)
            income_tax_return = get_object_or_404(
                IncomeTaxReturn,
                user=user,
                income_tax_return_year=income_tax_return_year
            )
            specific_year_data = ReportsPageSerializer(income_tax_return).data

            return Response(specific_year_data, status=status.HTTP_200_OK)
        else:
            current_year_obj = IncomeTaxCurrentYear().get_current_income_tax_return_year()
            if not current_year_obj:
                return Response({"error": "No current year found"}, status=status.HTTP_404_NOT_FOUND)
            current_income_tax_return = IncomeTaxReturn.objects.filter(
                user=user, income_tax_return_year=current_year_obj).first()
            graph_income_tax_returns = IncomeTaxReturn.objects.filter(user=user).select_related(
                'income_tax_return_year', 'user__income_tax_profile')

            graph_data = ReportsPageGraphDataSerializer(graph_income_tax_returns, many=True).data

            current_year_data = ReportsPageSerializer(current_income_tax_return).data

            response_data = {
                "income_tax_return_year_data": current_year_data,
                "graph_data": graph_data
            }
            return Response(response_data, status=status.HTTP_200_OK)


class IncomeTaxReturnYearListAPIView(generics.ListAPIView):
    queryset = IncomeTaxReturnYears.objects.all()
    serializer_class = IncomeTaxReturnYearSerializer
    permission_classes = [IsAuthenticated]


class Download26ASAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_year_name = unquote(self.kwargs['income_tax_return_year_name'])
        income_tax_return = get_object_or_404(
            IncomeTaxReturn,
            user=user,
            income_tax_return_year__name=income_tax_return_year_name
        )
        form_26as_pdf = income_tax_return.tds_pdf
        if not form_26as_pdf:
            raise Http404("Form 26AS file not found for this year.")
        pdf_url = request.build_absolute_uri(form_26as_pdf.url)

        return Response({"26as_pdf_url": pdf_url})


class DownloadAISAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_year_name = unquote(self.kwargs['income_tax_return_year_name'])
        income_tax_return = get_object_or_404(
            IncomeTaxReturn,
            user=user,
            income_tax_return_year__name=income_tax_return_year_name
        )
        ais_pdf = income_tax_return.ais_pdf
        if not ais_pdf:
            raise Http404("AIS file not found for this year.")
        pdf_url = request.build_absolute_uri(ais_pdf.url)

        return Response({"ais_pdf_url": pdf_url})


class DownloadTISAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_year_name = unquote(self.kwargs['income_tax_return_year_name'])
        income_tax_return = get_object_or_404(
            IncomeTaxReturn,
            user=user,
            income_tax_return_year__name=income_tax_return_year_name
        )
        tis_pdf = income_tax_return.tis_pdf
        if not tis_pdf:
            raise Http404("TIS file not found for this year.")
        pdf_url = request.build_absolute_uri(tis_pdf.url)

        return Response({"pdf_url": pdf_url})


class TaxRefundAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxSummarySerializer

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs.get('income_tax_return_id')
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        current_income_tax_return = get_object_or_404(IncomeTaxReturn, id=income_tax_return_id, user=request.user)
        serializer = self.get_serializer(current_income_tax_return)
        return Response(serializer.data, status=200)


class ComputationsOldRegimeApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    tax_calculator = IncomeTaxCalculations()

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        user = request.user

        try:
            tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        except IncomeTaxReturn.DoesNotExist:
            return Response({"detail": "Income tax return not found."}, status=404)

        salary_incomes = SalaryIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        rental_incomes = RentalIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        capital_gains = CapitalGains.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        business_incomes = BusinessIncome.objects.filter(income_tax__user=user,
                                                         income_tax_return_id=income_tax_return_id)
        interest_incomes = InterestIncome.objects.filter(income_tax__user=user,
                                                         income_tax_return_id=income_tax_return_id)
        dividend_incomes = DividendIncome.objects.filter(income_tax__user=user,
                                                         income_tax_return_id=income_tax_return_id)
        income_from_bettings = IncomeFromBetting.objects.filter(income_tax__user=user,
                                                                income_tax_return_id=income_tax_return_id)
        exempt_incomes = ExemptIncome.objects.filter(income_tax_return_id=income_tax_return_id)
        agriculture_incomes = AgricultureIncome.objects.filter(income_tax_return_id=income_tax_return_id)
        deductions = Deductions.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id).first()
        tds_deductions = TdsOrTcsDeduction.objects.filter(income_tax_return_id=income_tax_return_id,
                                                          income_tax__user=user)
        self_assessment_advance_tax = SelfAssesmentAndAdvanceTaxPaid.objects.filter(
            income_tax_return_id=income_tax_return_id, income_tax__user=user)

        tax_return_year = tax_return.income_tax_return_year
        filing_date = timezone.now().date()
        due_date = tax_return_year.due_date
        start_date = tax_return_year.start_date if tax_return_year else None
        end_date = tax_return_year.end_date if tax_return_year else None

        base_standard_deduction = Decimal('50000')

        salary_incomes_data_old, _, total_income_from_salaries_old, _ = self.tax_calculator.calculate_salary_income(
            salary_incomes, base_standard_deduction)

        rental_incomes_data, total_rental_income_old, _ = self.tax_calculator.calculate_rental_income(rental_incomes)

        total_capital_gains_income, long_term_capital_gains_112A, long_term_capital_gains_others, short_term_capital_gains = self.tax_calculator.calculate_capital_gains(
            capital_gains)

        business_incomes_data, total_income_from_business = self.tax_calculator.calculate_business_income(
            business_incomes)

        total_interest_income = sum([i.interest_amount for i in interest_incomes])
        total_dividend_income = sum([d.amount for d in dividend_incomes])
        total_winnings_income = sum([w.amount for w in income_from_bettings])

        total_exempt_income = sum([e.amount for e in exempt_incomes])
        total_net_income_from_agriculture = sum([agri_income.net_income for agri_income in agriculture_incomes])
        total_combined_exempt_income = total_exempt_income + total_net_income_from_agriculture

        deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum = self.tax_calculator.calculate_deductions(
            deductions, interest_incomes)

        total_deduction_amount = deduction_80c_sum + nps_contribution_sum + medical_premium_sum + interest_on_savings_sum

        total_tds_or_tcs, total_self_assessment_tax, total_advance_tax = self.tax_calculator.calculate_tds_advance_tax(
            tds_deductions, self_assessment_advance_tax, start_date, end_date)
        tax_paid_old = total_tds_or_tcs + total_self_assessment_tax + total_advance_tax

        gross_total_income_old = self.tax_calculator.calculate_gross_total_income(
            total_income_from_salaries_old, total_rental_income_old, total_income_from_business,
            total_capital_gains_income,
            total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income)

        total_income_old = gross_total_income_old - total_deduction_amount

        tax_liability_old = self.tax_calculator.calculate_tax_liability_old_regime(gross_total_income_old)

        surcharge_old = self.tax_calculator.calculate_surcharge(gross_total_income_old, tax_liability_old, regime="old")

        tax_rebate_old = self.tax_calculator.calculate_tax_rebate_old_regime(gross_total_income_old, tax_liability_old)

        cess_old = self.tax_calculator.calculate_cess(tax_liability_old, surcharge_old, tax_rebate_old)

        net_tax_payable_old = tax_liability_old + surcharge_old - tax_rebate_old + cess_old

        balance_tax_to_be_paid_old = net_tax_payable_old - total_advance_tax - total_tds_or_tcs

        interest_234A_old = self.tax_calculator.calculate_interest_234A(balance_tax_to_be_paid_old, filing_date,
                                                                        due_date)
        interest_234B_old = self.tax_calculator.calculate_interest_234B(balance_tax_to_be_paid_old, total_advance_tax,
                                                                        net_tax_payable_old)
        interest_234C_old = self.tax_calculator.calculate_interest_234C(balance_tax_to_be_paid_old, total_advance_tax,
                                                                        net_tax_payable_old)
        total_interest_234_old = interest_234A_old + interest_234B_old + interest_234C_old

        penalty_us_234F_old = self.tax_calculator.calculate_penalty_us_234F(total_income_old, filing_date, due_date)

        tax_payable_old = balance_tax_to_be_paid_old + total_interest_234_old + penalty_us_234F_old

        old_regime_data = {
            "salary_incomes": salary_incomes_data_old,
            "total_income_from_salaries": self.tax_calculator.round_off_decimal(total_income_from_salaries_old),
            "rental_incomes": rental_incomes_data,
            "long_term_capital_gain_u_s_112a": self.tax_calculator.round_off_decimal(long_term_capital_gains_112A),
            "long_term_capital_gain_others": self.tax_calculator.round_off_decimal(long_term_capital_gains_others),
            "short_term_capital_gain": self.tax_calculator.round_off_decimal(short_term_capital_gains),
            "total_capital_gains_income": self.tax_calculator.round_off_decimal(total_capital_gains_income),
            "business_incomes": business_incomes_data,
            "total_income_from_business": self.tax_calculator.round_off_decimal(total_income_from_business),
            "interest_income": self.tax_calculator.round_off_decimal(total_interest_income),
            "dividend_income": self.tax_calculator.round_off_decimal(total_dividend_income),
            "winnings_lotteries_games_bettings": self.tax_calculator.round_off_decimal(total_winnings_income),
            "total_of_other_incomes": self.tax_calculator.round_off_decimal(
                total_interest_income + total_dividend_income + total_winnings_income),
            "exempt_income": self.tax_calculator.round_off_decimal(total_exempt_income),
            "net_income_from_agriculture": self.tax_calculator.round_off_decimal(total_net_income_from_agriculture),
            "total_exempt_income": self.tax_calculator.round_off_decimal(total_combined_exempt_income),
            "deduction_u_s_80c": self.tax_calculator.round_off_decimal(deduction_80c_sum),
            "nps_contribution_u_s_ccd": self.tax_calculator.round_off_decimal(nps_contribution_sum),
            "80d_medical_insurance_premium": self.tax_calculator.round_off_decimal(medical_premium_sum),
            "80tta_interest_on_savings_acc": self.tax_calculator.round_off_decimal(interest_on_savings_sum),
            "total_deduction_amount": self.tax_calculator.round_off_decimal(total_deduction_amount),
            "tds_or_tcs": self.tax_calculator.round_off_decimal(total_tds_or_tcs),
            "self_assessment_tax": self.tax_calculator.round_off_decimal(total_self_assessment_tax),
            "advance_tax": self.tax_calculator.round_off_decimal(total_advance_tax),
            "tax_paid": tax_paid_old,
            "gross_total_income": self.tax_calculator.round_off_decimal(gross_total_income_old),
            "total_income": self.tax_calculator.round_off_decimal(total_income_old),
            "tax_liability_at_normal_rates": self.tax_calculator.round_off_decimal(tax_liability_old),
            "tax_rebate": self.tax_calculator.round_off_decimal(tax_rebate_old),
            "surcharge": self.tax_calculator.round_off_decimal(surcharge_old),
            "cess": self.tax_calculator.round_off_decimal(cess_old),
            "net_tax_payable": self.tax_calculator.round_off_decimal(net_tax_payable_old),
            "balance_tax_to_be_paid": self.tax_calculator.round_off_decimal(balance_tax_to_be_paid_old),
            "interest_u_s_234a_b_c": self.tax_calculator.round_off_decimal(total_interest_234_old),
            "penalt_u_s_234f": self.tax_calculator.round_off_decimal(penalty_us_234F_old),
            "tax_payable": self.tax_calculator.round_off_decimal(tax_payable_old)
        }

        # Prepare the final response for old regime
        old_regime_data_serializable = self.tax_calculator.convert_to_json_serializable(old_regime_data)

        return Response({"old_regime": old_regime_data_serializable}, status=200)


class ComputationsNewRegimeApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    tax_calculator = IncomeTaxCalculations()

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        user = request.user
        try:
            tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        except IncomeTaxReturn.DoesNotExist:
            return Response({"detail": "Income tax return not found."}, status=404)

        salary_incomes = SalaryIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        rental_incomes = RentalIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        capital_gains = CapitalGains.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        business_incomes = BusinessIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        interest_incomes = InterestIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        dividend_incomes = DividendIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        income_from_bettings = IncomeFromBetting.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        exempt_incomes = ExemptIncome.objects.filter(income_tax_return_id=income_tax_return_id)
        agriculture_incomes = AgricultureIncome.objects.filter(income_tax_return_id=income_tax_return_id)
        deductions = Deductions.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id).first()
        tds_deductions = TdsOrTcsDeduction.objects.filter(income_tax_return_id=income_tax_return_id, income_tax__user=user)
        self_assessment_advance_tax = SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax_return_id=income_tax_return_id, income_tax__user=user)

        tax_return_year = tax_return.income_tax_return_year
        filing_date = timezone.now().date()
        due_date = tax_return_year.due_date
        start_date = tax_return_year.start_date if tax_return_year else None
        end_date = tax_return_year.end_date if tax_return_year else None

        base_standard_deduction = Decimal('50000')

        _, salary_incomes_data_new, _, total_income_from_salaries_new = self.tax_calculator.calculate_salary_income(
            salary_incomes, base_standard_deduction)

        rental_incomes_data, _, total_rental_income_new = self.tax_calculator.calculate_rental_income(rental_incomes)

        total_capital_gains_income, long_term_capital_gains_112A, long_term_capital_gains_others, short_term_capital_gains = self.tax_calculator.calculate_capital_gains(
            capital_gains)

        business_incomes_data, total_income_from_business = self.tax_calculator.calculate_business_income(business_incomes)

        total_interest_income = sum([i.interest_amount for i in interest_incomes])
        total_dividend_income = sum([d.amount for d in dividend_incomes])
        total_winnings_income = sum([w.amount for w in income_from_bettings])

        total_exempt_income = sum([e.amount for e in exempt_incomes])
        total_net_income_from_agriculture = sum([agri_income.net_income for agri_income in agriculture_incomes])
        total_combined_exempt_income = total_exempt_income + total_net_income_from_agriculture

        deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum = self.tax_calculator.calculate_deductions(
            deductions, interest_incomes)

        total_deduction_amount = deduction_80c_sum + nps_contribution_sum + medical_premium_sum + interest_on_savings_sum

        total_tds_or_tcs, total_self_assessment_tax, total_advance_tax = self.tax_calculator.calculate_tds_advance_tax(
            tds_deductions, self_assessment_advance_tax, start_date, end_date)
        tax_paid_new = total_tds_or_tcs + total_self_assessment_tax + total_advance_tax

        gross_total_income_new = self.tax_calculator.calculate_gross_total_income(
            total_income_from_salaries_new, total_rental_income_new, total_income_from_business, total_capital_gains_income,
            total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income)

        total_income_new = gross_total_income_new - total_deduction_amount

        tax_liability_new = self.tax_calculator.calculate_tax_liability_new_regime(gross_total_income_new)

        surcharge_new = self.tax_calculator.calculate_surcharge(gross_total_income_new, tax_liability_new, regime="new")

        tax_rebate_new = self.tax_calculator.calculate_tax_rebate_new_regime(gross_total_income_new, tax_liability_new)

        cess_new = self.tax_calculator.calculate_cess(tax_liability_new, surcharge_new, tax_rebate_new)

        net_tax_payable_new = tax_liability_new + surcharge_new - tax_rebate_new + cess_new

        balance_tax_to_be_paid_new = net_tax_payable_new - total_advance_tax - total_tds_or_tcs

        interest_234A_new = self.tax_calculator.calculate_interest_234A(balance_tax_to_be_paid_new, filing_date, due_date)
        interest_234B_new = self.tax_calculator.calculate_interest_234B(balance_tax_to_be_paid_new, total_advance_tax, net_tax_payable_new)
        interest_234C_new = self.tax_calculator.calculate_interest_234C(balance_tax_to_be_paid_new, total_advance_tax, net_tax_payable_new)
        total_interest_234_new = interest_234A_new + interest_234B_new + interest_234C_new

        penalty_us_234F_new = self.tax_calculator.calculate_penalty_us_234F(total_income_new, filing_date, due_date)

        tax_payable_new = balance_tax_to_be_paid_new + total_interest_234_new + penalty_us_234F_new

        new_regime_data = {
            "salary_incomes": salary_incomes_data_new,
            "total_income_from_salaries": self.tax_calculator.round_off_decimal(total_income_from_salaries_new),
            "rental_incomes": rental_incomes_data,
            "long_term_capital_gain_u_s_112A": self.tax_calculator.round_off_decimal(long_term_capital_gains_112A),
            "long_term_capital_gain_others": self.tax_calculator.round_off_decimal(long_term_capital_gains_others),
            "short_term_capital_gain": self.tax_calculator.round_off_decimal(short_term_capital_gains),
            "total_capital_gains_income": self.tax_calculator.round_off_decimal(total_capital_gains_income),
            "business_incomes": business_incomes_data,
            "total_income_from_business": self.tax_calculator.round_off_decimal(total_income_from_business),
            "interest_income": self.tax_calculator.round_off_decimal(total_interest_income),
            "dividend_income": self.tax_calculator.round_off_decimal(total_dividend_income),
            "winnings_Lotteries_games_bettings": self.tax_calculator.round_off_decimal(total_winnings_income),
            "total_of_other_incomes": self.tax_calculator.round_off_decimal(total_interest_income + total_dividend_income + total_winnings_income),
            "exempt_income": self.tax_calculator.round_off_decimal(total_exempt_income),
            "net_income_from_agriculture": self.tax_calculator.round_off_decimal(total_net_income_from_agriculture),
            "total_exempt_income": self.tax_calculator.round_off_decimal(total_combined_exempt_income),
            "deduction_u_s_80C": self.tax_calculator.round_off_decimal(deduction_80c_sum),
            "nps_contribution_u_s_ccd": self.tax_calculator.round_off_decimal(nps_contribution_sum),
            "80d_medical_insurance_premium": self.tax_calculator.round_off_decimal(medical_premium_sum),
            "80tta_interest_on_savings_acc": self.tax_calculator.round_off_decimal(interest_on_savings_sum),
            "total_deduction_amount": self.tax_calculator.round_off_decimal(total_deduction_amount),
            "tds_or_tcs": self.tax_calculator.round_off_decimal(total_tds_or_tcs),
            "self_assessment_tax": self.tax_calculator.round_off_decimal(total_self_assessment_tax),
            "advance_tax": self.tax_calculator.round_off_decimal(total_advance_tax),
            "tax_paid": tax_paid_new,
            "gross_total_income": self.tax_calculator.round_off_decimal(gross_total_income_new),
            "total_income": self.tax_calculator.round_off_decimal(total_income_new),
            "tax_liability_at_normal_rates": self.tax_calculator.round_off_decimal(tax_liability_new),
            "tax_rebate": self.tax_calculator.round_off_decimal(tax_rebate_new),
            "surcharge": self.tax_calculator.round_off_decimal(surcharge_new),
            "cess": self.tax_calculator.round_off_decimal(cess_new),
            "net_tax_payable": self.tax_calculator.round_off_decimal(net_tax_payable_new),
            "balance_tax_to_be_Paid": self.tax_calculator.round_off_decimal(balance_tax_to_be_paid_new),
            "interest_u_s_234a_b_c": self.tax_calculator.round_off_decimal(total_interest_234_new),
            "penalty_u_s_234f": self.tax_calculator.round_off_decimal(penalty_us_234F_new),
            "tax_payable": self.tax_calculator.round_off_decimal(tax_payable_new)
        }
        new_regime_data_serializable = self.tax_calculator.convert_to_json_serializable(new_regime_data)

        return Response({"new_regime": new_regime_data_serializable}, status=200)


class SummaryPageApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        user = request.user

        try:
            tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        except IncomeTaxReturn.DoesNotExist:
            return Response({"detail": "Income tax return not found."}, status=404)

        salary_incomes = SalaryIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        rental_incomes = RentalIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        capital_gains = CapitalGains.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)
        business_incomes = BusinessIncome.objects.filter(income_tax__user=user,
                                                         income_tax_return_id=income_tax_return_id)
        interest_incomes = InterestIncome.objects.filter(income_tax__user=user,
                                                         income_tax_return_id=income_tax_return_id)
        dividend_incomes = DividendIncome.objects.filter(income_tax__user=user,
                                                         income_tax_return_id=income_tax_return_id)
        income_from_bettings = IncomeFromBetting.objects.filter(income_tax__user=user,
                                                                income_tax_return_id=income_tax_return_id)
        exempt_incomes = ExemptIncome.objects.filter(income_tax_return_id=income_tax_return_id)
        agriculture_incomes = AgricultureIncome.objects.filter(income_tax_return_id=income_tax_return_id)
        deductions = Deductions.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id).first()
        tds_deductions = TdsOrTcsDeduction.objects.filter(income_tax_return_id=income_tax_return_id,
                                                          income_tax__user=user)
        self_assessment_advance_tax = SelfAssesmentAndAdvanceTaxPaid.objects.filter(
            income_tax_return_id=income_tax_return_id, income_tax__user=user)

        tax_return_year = tax_return.income_tax_return_year
        filing_date = timezone.now().date()
        due_date = tax_return_year.due_date
        start_date = tax_return_year.start_date if tax_return_year else None
        end_date = tax_return_year.end_date if tax_return_year else None

        calc = IncomeTaxCalculations()

        base_standard_deduction = Decimal('50000')
        salary_incomes_data_old, _, total_income_from_salaries_old, _ = calc.calculate_salary_income(salary_incomes,
                                                                                                     base_standard_deduction)
        rental_incomes_data, total_rental_income_old, _ = calc.calculate_rental_income(rental_incomes)
        total_capital_gains_income, long_term_capital_gains_112A, long_term_capital_gains_others, short_term_capital_gains = calc.calculate_capital_gains(
            capital_gains)
        business_incomes_data, total_income_from_business = calc.calculate_business_income(business_incomes)
        total_interest_income = sum([i.interest_amount for i in interest_incomes])
        total_dividend_income = sum([d.amount for d in dividend_incomes])
        total_winnings_income = sum([w.amount for w in income_from_bettings])
        total_exempt_income = sum([e.amount for e in exempt_incomes])
        total_net_income_from_agriculture = sum([agri_income.net_income for agri_income in agriculture_incomes])
        total_combined_exempt_income = total_exempt_income + total_net_income_from_agriculture
        deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum = calc.calculate_deductions(
            deductions, interest_incomes)
        total_deduction_amount = deduction_80c_sum + nps_contribution_sum + medical_premium_sum + interest_on_savings_sum
        total_tds_or_tcs, total_self_assessment_tax, total_advance_tax = calc.calculate_tds_advance_tax(tds_deductions,
                                                                                                        self_assessment_advance_tax,
                                                                                                        start_date,
                                                                                                        end_date)
        gross_total_income_old = calc.calculate_gross_total_income(total_income_from_salaries_old,
                                                                   total_rental_income_old, total_income_from_business,
                                                                   total_capital_gains_income, total_interest_income,
                                                                   total_dividend_income, total_winnings_income,
                                                                   total_combined_exempt_income)
        total_income_old = gross_total_income_old - total_deduction_amount
        tax_liability_old = calc.calculate_tax_liability_old_regime(gross_total_income_old)
        surcharge_old = calc.calculate_surcharge(gross_total_income_old, tax_liability_old, regime="old")
        tax_rebate_old = calc.calculate_tax_rebate_old_regime(gross_total_income_old, tax_liability_old)
        cess_old = calc.calculate_cess(tax_liability_old, surcharge_old, tax_rebate_old)
        net_tax_payable_old = tax_liability_old + surcharge_old - tax_rebate_old + cess_old
        balance_tax_to_be_paid_old = net_tax_payable_old - total_advance_tax - total_tds_or_tcs
        interest_234A_old = calc.calculate_interest_234A(balance_tax_to_be_paid_old, filing_date, due_date)
        interest_234B_old = calc.calculate_interest_234B(balance_tax_to_be_paid_old, total_advance_tax,
                                                         net_tax_payable_old)
        interest_234C_old = calc.calculate_interest_234C(balance_tax_to_be_paid_old, total_advance_tax,
                                                         net_tax_payable_old)
        total_interest_234_old = interest_234A_old + interest_234B_old + interest_234C_old
        penalty_us_234F_old = calc.calculate_penalty_us_234F(total_income_old, filing_date, due_date)
        tax_payable_old = balance_tax_to_be_paid_old + total_interest_234_old + penalty_us_234F_old

        _, salary_incomes_data_new, _, total_income_from_salaries_new = calc.calculate_salary_income(salary_incomes,
                                                                                                     base_standard_deduction)
        gross_total_income_new = calc.calculate_gross_total_income(total_income_from_salaries_new,
                                                                   total_rental_income_old, total_income_from_business,
                                                                   total_capital_gains_income, total_interest_income,
                                                                   total_dividend_income, total_winnings_income,
                                                                   total_combined_exempt_income)
        total_income_new = gross_total_income_new - total_deduction_amount
        tax_liability_new = calc.calculate_tax_liability_new_regime(gross_total_income_new)
        surcharge_new = calc.calculate_surcharge(gross_total_income_new, tax_liability_new, regime="new")
        tax_rebate_new = calc.calculate_tax_rebate_new_regime(gross_total_income_new, tax_liability_new)
        cess_new = calc.calculate_cess(tax_liability_new, surcharge_new, tax_rebate_new)
        net_tax_payable_new = tax_liability_new + surcharge_new - tax_rebate_new + cess_new
        balance_tax_to_be_paid_new = net_tax_payable_new - total_advance_tax - total_tds_or_tcs
        interest_234A_new = calc.calculate_interest_234A(balance_tax_to_be_paid_new, filing_date, due_date)
        interest_234B_new = calc.calculate_interest_234B(balance_tax_to_be_paid_new, total_advance_tax,
                                                         net_tax_payable_new)
        interest_234C_new = calc.calculate_interest_234C(balance_tax_to_be_paid_new, total_advance_tax,
                                                         net_tax_payable_new)
        total_interest_234_new = interest_234A_new + interest_234B_new + interest_234C_new
        penalty_us_234F_new = calc.calculate_penalty_us_234F(total_income_new, filing_date, due_date)
        tax_payable_new = balance_tax_to_be_paid_new + total_interest_234_new + penalty_us_234F_new

        total_rental_income_sum = sum([rental_income.annual_rent for rental_income in rental_incomes])

        interest_and_penalty_old = total_interest_234_old + penalty_us_234F_old
        interest_and_penalty_new = total_interest_234_new + penalty_us_234F_new

        response_data = {
            "old_regime": {
                "total_income_from_salaries": calc.round_off_decimal(total_income_from_salaries_old),
                "total_rental_income": calc.round_off_decimal(total_rental_income_sum),
                "total_capital_gains_income": calc.round_off_decimal(total_capital_gains_income),
                "total_income_from_business": calc.round_off_decimal(total_income_from_business),
                "total_of_other_incomes": calc.round_off_decimal(
                    total_interest_income + total_dividend_income + total_winnings_income),
                "total_exempt_income": calc.round_off_decimal(total_combined_exempt_income),
                "total_deduction_amount": calc.round_off_decimal(total_deduction_amount),
                "tds_or_tcs": calc.round_off_decimal(total_tds_or_tcs),
                "self_assessment_tax": calc.round_off_decimal(total_self_assessment_tax),
                "advance_tax": calc.round_off_decimal(total_advance_tax),
                "gross_total_income": calc.round_off_decimal(gross_total_income_old),
                "total_income": calc.round_off_decimal(total_income_old),
                "tax_liability_at_normal_rates": calc.round_off_decimal(tax_liability_old),
                "net_tax_payable": calc.round_off_decimal(net_tax_payable_old),
                "balance_tax_to_be_paid": calc.round_off_decimal(balance_tax_to_be_paid_old),
                "interest_and_penalty": calc.round_off_decimal(interest_and_penalty_old),
                "tax_payable": calc.round_off_decimal(tax_payable_old),

            },
            "new_regime": {
                "total_income_from_salaries": calc.round_off_decimal(total_income_from_salaries_new),
                "total_rental_income": calc.round_off_decimal(total_rental_income_sum),
                "total_capital_gains_income": calc.round_off_decimal(total_capital_gains_income),
                "total_income_from_business": calc.round_off_decimal(total_income_from_business),
                "total_of_other_incomes": calc.round_off_decimal(
                    total_interest_income + total_dividend_income + total_winnings_income),
                "total_exempt_income": calc.round_off_decimal(total_combined_exempt_income),
                "total_deduction_amount": calc.round_off_decimal(total_deduction_amount),
                "tds_or_tcs": calc.round_off_decimal(total_tds_or_tcs),
                "self_assessment_tax": calc.round_off_decimal(total_self_assessment_tax),
                "advance_tax": calc.round_off_decimal(total_advance_tax),
                "gross_total_income": calc.round_off_decimal(gross_total_income_new),
                "total_income": calc.round_off_decimal(total_income_new),
                "tax_liability_at_normal_rates": calc.round_off_decimal(tax_liability_new),
                "net_tax_payable": calc.round_off_decimal(net_tax_payable_new),
                "balance_tax_to_be_paid": calc.round_off_decimal(balance_tax_to_be_paid_new),
                "interest_and_penalty": calc.round_off_decimal(interest_and_penalty_new),
                "tax_payable": calc.round_off_decimal(tax_payable_new),

            }
        }

        return Response(response_data, status=200)


class ComputationsCreateApi(generics.CreateAPIView):
    serializer_class = ComputationsSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)
        income_tax_return = get_object_or_404(IncomeTaxReturn, id=income_tax_return_id)
        data = request.data.copy()
        regime_type_str = data.get('regime_type', '').lower()

        if regime_type_str == 'new':
            regime_type = Computations.New
        elif regime_type_str == 'old':
            regime_type = Computations.Old
        else:
            return Response({'error': 'Invalid regime type. Use "new" or "old".'}, status=status.HTTP_400_BAD_REQUEST)

        computation = Computations.objects.filter(income_tax_return=income_tax_return, regime_type=regime_type).first()

        if computation:
            serializer = self.get_serializer(computation, data=data, partial=True)
            status_code = status.HTTP_200_OK
        else:
            serializer = self.get_serializer(data=data)
            status_code = status.HTTP_201_CREATED

        serializer.is_valid(raise_exception=True)
        serializer.save(income_tax_return=income_tax_return)

        return Response(serializer.data, status=status_code)


class GeneratePdfMixin:

    def render_to_pdf(self, template_src, context_dict):
        template = get_template(template_src)
        html = template.render(context_dict)
        result = BytesIO()

        pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)

        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        return None


class IncomeTaxPdfView(generics.GenericAPIView, GeneratePdfMixin):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        try:
            tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=request.user)
            profile = tax_return.user.income_tax_profile
        except IncomeTaxReturn.DoesNotExist:
            return HttpResponse("Invalid Income Tax Return ID or Unauthorized access.", status=404)

        salary_incomes = tax_return.salary_incomes.all()
        rental_incomes = tax_return.rental_incomes.all()
        capital_gains = tax_return.capital_gains.all()
        business_incomes = tax_return.business_income.all()
        interest_incomes = tax_return.exempt_incomes.all()
        dividend_incomes = tax_return.dividend_income.all()
        income_from_bettings = tax_return.income_from_betting.all()
        exempt_incomes = tax_return.exempt_incomes_agriculture.all()
        agriculture_incomes = tax_return.agriculture_income.all()

        deductions = None
        try:
            deductions = tax_return.deductions
        except Deductions.DoesNotExist:
            deductions = None
        tds_deductions = tax_return.tds_or_tcs_deduction.all()
        self_assessment_advance_tax = tax_return.self_assesment_and_advance_tax_paid.all()

        calc = IncomeTaxCalculations()
        base_standard_deduction = Decimal('50000')

        salary_incomes_data_old, _, total_income_from_salaries_old, _ = calc.calculate_salary_income(salary_incomes, base_standard_deduction)
        rental_incomes_data, total_rental_income_old, _ = calc.calculate_rental_income(rental_incomes)
        total_capital_gains_income, _, _, _ = calc.calculate_capital_gains(capital_gains)
        _, total_income_from_business = calc.calculate_business_income(business_incomes)
        total_interest_income = sum([i.interest_amount for i in interest_incomes])
        total_dividend_income = sum([d.amount for d in dividend_incomes])
        total_winnings_income = sum([w.amount for w in income_from_bettings])
        total_exempt_income = sum([e.amount for e in exempt_incomes])
        total_net_income_from_agriculture = sum([agri_income.net_income for agri_income in agriculture_incomes])
        total_combined_exempt_income = total_exempt_income + total_net_income_from_agriculture
        if deductions:
            deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum = calc.calculate_deductions(
                deductions, interest_incomes)
            total_deduction_amount = deduction_80c_sum + nps_contribution_sum + medical_premium_sum + interest_on_savings_sum
        else:
            total_deduction_amount = Decimal('0')

        total_tds_or_tcs, total_self_assessment_tax, total_advance_tax = calc.calculate_tds_advance_tax(tds_deductions, self_assessment_advance_tax, tax_return.income_tax_return_year.start_date, tax_return.income_tax_return_year.end_date)
        gross_total_income_old = calc.calculate_gross_total_income(total_income_from_salaries_old, total_rental_income_old, total_income_from_business, total_capital_gains_income, total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income)
        total_income_old = gross_total_income_old - total_deduction_amount
        tax_liability_old = calc.calculate_tax_liability_old_regime(gross_total_income_old)
        surcharge_old = calc.calculate_surcharge(gross_total_income_old, tax_liability_old, regime="old")
        tax_rebate_old = calc.calculate_tax_rebate_old_regime(gross_total_income_old, tax_liability_old)
        cess_old = calc.calculate_cess(tax_liability_old, surcharge_old, tax_rebate_old)
        net_tax_payable_old = tax_liability_old + surcharge_old - tax_rebate_old + cess_old
        balance_tax_to_be_paid_old = net_tax_payable_old - total_advance_tax - total_tds_or_tcs
        total_interest_234_old = calc.calculate_interest_234A(balance_tax_to_be_paid_old, timezone.now().date(), tax_return.income_tax_return_year.due_date) + \
                                 calc.calculate_interest_234B(balance_tax_to_be_paid_old, total_advance_tax, net_tax_payable_old) + \
                                 calc.calculate_interest_234C(balance_tax_to_be_paid_old, total_advance_tax, net_tax_payable_old)
        penalty_us_234F_old = calc.calculate_penalty_us_234F(total_income_old, timezone.now().date(), tax_return.income_tax_return_year.due_date)
        tax_payable_old = balance_tax_to_be_paid_old + total_interest_234_old + penalty_us_234F_old

        _, salary_incomes_data_new, _, total_income_from_salaries_new = calc.calculate_salary_income(salary_incomes, base_standard_deduction)
        gross_total_income_new = calc.calculate_gross_total_income(total_income_from_salaries_new, total_rental_income_old, total_income_from_business, total_capital_gains_income, total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income)
        total_income_new = gross_total_income_new - total_deduction_amount
        tax_liability_new = calc.calculate_tax_liability_new_regime(gross_total_income_new)
        surcharge_new = calc.calculate_surcharge(gross_total_income_new, tax_liability_new, regime="new")
        tax_rebate_new = calc.calculate_tax_rebate_new_regime(gross_total_income_new, tax_liability_new)
        cess_new = calc.calculate_cess(tax_liability_new, surcharge_new, tax_rebate_new)
        net_tax_payable_new = tax_liability_new + surcharge_new - tax_rebate_new + cess_new
        balance_tax_to_be_paid_new = net_tax_payable_new - total_advance_tax - total_tds_or_tcs
        total_interest_234_new = calc.calculate_interest_234A(balance_tax_to_be_paid_new, timezone.now().date(), tax_return.income_tax_return_year.due_date) + \
                                 calc.calculate_interest_234B(balance_tax_to_be_paid_new, total_advance_tax, net_tax_payable_new) + \
                                 calc.calculate_interest_234C(balance_tax_to_be_paid_new, total_advance_tax, net_tax_payable_new)
        penalty_us_234F_new = calc.calculate_penalty_us_234F(total_income_new, timezone.now().date(), tax_return.income_tax_return_year.due_date)
        tax_payable_new = balance_tax_to_be_paid_new + total_interest_234_new + penalty_us_234F_new

        total_rental_income_sum = sum([rental_income.annual_rent for rental_income in rental_incomes])

        interest_and_penalty_old = total_interest_234_old + penalty_us_234F_old
        interest_and_penalty_new = total_interest_234_new + penalty_us_234F_new

        context = {
            "old_regime": {
                "salary_income": calc.round_off_decimal(total_income_from_salaries_old),
                "rental_income": calc.round_off_decimal(total_rental_income_sum),
                "capital_gains_income": calc.round_off_decimal(total_capital_gains_income),
                "business_income": calc.round_off_decimal(total_income_from_business),
                "exempt_income": calc.round_off_decimal(total_combined_exempt_income),
                "gross_total_income": calc.round_off_decimal(gross_total_income_old),
                "deductions": calc.round_off_decimal(total_deduction_amount),
                "total_income": calc.round_off_decimal(total_income_old),
                "tax_on_total_income": calc.round_off_decimal(tax_liability_old),
                "taxes_paid": calc.round_off_decimal(total_tds_or_tcs),
                "interest_and_penalties": calc.round_off_decimal(interest_and_penalty_old),
                "tax_payable": calc.round_off_decimal(tax_payable_old),
            },
            "new_regime": {
                "salary_income": calc.round_off_decimal(total_income_from_salaries_new),
                "rental_income": calc.round_off_decimal(total_rental_income_sum),
                "capital_gains_income": calc.round_off_decimal(total_capital_gains_income),
                "business_income": calc.round_off_decimal(total_income_from_business),
                "exempt_income": calc.round_off_decimal(total_combined_exempt_income),
                "gross_total_income": calc.round_off_decimal(gross_total_income_new),
                "deductions": calc.round_off_decimal(total_deduction_amount),
                "total_income": calc.round_off_decimal(total_income_new),
                "tax_on_total_income": calc.round_off_decimal(tax_liability_new),
                "taxes_paid": calc.round_off_decimal(total_tds_or_tcs),
                "interest_and_penalties": calc.round_off_decimal(interest_and_penalty_new),
                "tax_payable": calc.round_off_decimal(tax_payable_new),
            },
            "recommended": {
                "regime_type": "New Regime" if net_tax_payable_new < net_tax_payable_old else "Old Regime",
                "savings": abs(net_tax_payable_new - net_tax_payable_old),
            }
        }

        pdf = self.render_to_pdf('itr_summary_report.html', context)

        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"{slugify(profile.user.username)}-income-tax-report.pdf"
            content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response

        return HttpResponse("Error generating PDF", status=500)


class IncometaxComputationsOldPdfView(generics.GenericAPIView, GeneratePdfMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        try:
            tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=request.user)
        except IncomeTaxReturn.DoesNotExist:
            return HttpResponse("Invalid Income Tax Return ID or Unauthorized access.", status=404)

        calc = IncomeTaxCalculations()
        base_standard_deduction = Decimal('50000')

        salary_incomes = tax_return.salary_incomes.all()
        rental_incomes = tax_return.rental_incomes.all()
        capital_gains = tax_return.capital_gains.all()
        business_incomes = tax_return.business_income.all()
        interest_incomes = tax_return.exempt_incomes.all()
        dividend_incomes = tax_return.dividend_income.all()
        exempt_incomes = tax_return.exempt_incomes_agriculture.all()
        agriculture_incomes = tax_return.agriculture_income.all()

        salary_incomes_data_old, _, total_income_from_salaries_old, _ = calc.calculate_salary_income(salary_incomes, base_standard_deduction)
        rental_incomes_data, total_rental_income_old, _ = calc.calculate_rental_income(rental_incomes)
        total_capital_gains_income, long_term_capital_gains_112A, long_term_capital_gains_others, short_term_capital_gains = calc.calculate_capital_gains(capital_gains)
        business_incomes_data, total_income_from_business = calc.calculate_business_income(business_incomes)
        total_interest_income = sum([i.interest_amount for i in interest_incomes])
        total_dividend_income = sum([d.amount for d in dividend_incomes])
        total_winnings_income = 0  # Assuming you handle this elsewhere
        total_exempt_income = sum([e.amount for e in exempt_incomes])
        total_net_income_from_agriculture = sum([agri_income.net_income for agri_income in agriculture_incomes])
        total_combined_exempt_income = total_exempt_income + total_net_income_from_agriculture

        deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum = calc.calculate_deductions(tax_return.deductions, interest_incomes)
        total_deduction_amount = deduction_80c_sum + nps_contribution_sum + medical_premium_sum + interest_on_savings_sum

        total_tds_or_tcs, total_self_assessment_tax, total_advance_tax = calc.calculate_tds_advance_tax(tax_return.tds_or_tcs_deduction.all(), tax_return.self_assesment_and_advance_tax_paid.all(), tax_return.income_tax_return_year.start_date, tax_return.income_tax_return_year.end_date)
        gross_total_income_old = calc.calculate_gross_total_income(total_income_from_salaries_old, total_rental_income_old, total_income_from_business, total_capital_gains_income, total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income)
        total_income_old = gross_total_income_old - total_deduction_amount
        tax_liability_old = calc.calculate_tax_liability_old_regime(gross_total_income_old)
        surcharge_old = calc.calculate_surcharge(gross_total_income_old, tax_liability_old, regime="old")
        tax_rebate_old = calc.calculate_tax_rebate_old_regime(gross_total_income_old, tax_liability_old)
        cess_old = calc.calculate_cess(tax_liability_old, surcharge_old, tax_rebate_old)
        net_tax_payable_old = tax_liability_old + surcharge_old - tax_rebate_old + cess_old
        balance_tax_to_be_paid_old = net_tax_payable_old - total_advance_tax - total_tds_or_tcs
        total_interest_234_old = calc.calculate_interest_234A(balance_tax_to_be_paid_old, timezone.now().date(), tax_return.income_tax_return_year.due_date) + \
                                 calc.calculate_interest_234B(balance_tax_to_be_paid_old, total_advance_tax, net_tax_payable_old) + \
                                 calc.calculate_interest_234C(balance_tax_to_be_paid_old, total_advance_tax, net_tax_payable_old)
        penalty_us_234F_old = calc.calculate_penalty_us_234F(total_income_old, timezone.now().date(), tax_return.income_tax_return_year.due_date)
        tax_payable_old = balance_tax_to_be_paid_old + total_interest_234_old + penalty_us_234F_old

        context ={
        "old_regime_data" : {
            "salary_incomes": salary_incomes_data_old,
            "total_income_from_salaries": calc.round_off_decimal(total_income_from_salaries_old),
            "rental_incomes": rental_incomes_data,
            "long_term_capital_gain_u_s_112a": calc.round_off_decimal(long_term_capital_gains_112A),
            "long_term_capital_gain_others": calc.round_off_decimal(long_term_capital_gains_others),
            "short_term_capital_gain": calc.round_off_decimal(short_term_capital_gains),
            "total_capital_gains_income": calc.round_off_decimal(total_capital_gains_income),
            "business_incomes": business_incomes_data,
            "total_income_from_business": calc.round_off_decimal(total_income_from_business),
            "interest_income": calc.round_off_decimal(total_interest_income),
            "dividend_income": calc.round_off_decimal(total_dividend_income),
            "winnings_lotteries_games_bettings": calc.round_off_decimal(total_winnings_income),
            "total_of_other_incomes": calc.round_off_decimal(total_interest_income + total_dividend_income + total_winnings_income),
            "exempt_income": calc.round_off_decimal(total_exempt_income),
            "net_income_from_agriculture": calc.round_off_decimal(total_net_income_from_agriculture),
            "total_exempt_income": calc.round_off_decimal(total_combined_exempt_income),
            "deduction_u_s_80c": calc.round_off_decimal(deduction_80c_sum),
            "nps_contribution_u_s_ccd": calc.round_off_decimal(nps_contribution_sum),
            "80d_medical_insurance_premium": calc.round_off_decimal(medical_premium_sum),
            "80tta_interest_on_savings_acc": calc.round_off_decimal(interest_on_savings_sum),
            "total_deduction_amount": calc.round_off_decimal(total_deduction_amount),
            "tds_or_tcs": calc.round_off_decimal(total_tds_or_tcs),
            "self_assessment_tax": calc.round_off_decimal(total_self_assessment_tax),
            "advance_tax": calc.round_off_decimal(total_advance_tax),
            "gross_total_income": calc.round_off_decimal(gross_total_income_old),
            "total_income": calc.round_off_decimal(total_income_old),
            "tax_liability_at_normal_rates": calc.round_off_decimal(tax_liability_old),
            "tax_rebate": calc.round_off_decimal(tax_rebate_old),
            "surcharge": calc.round_off_decimal(surcharge_old),
            "cess": calc.round_off_decimal(cess_old),
            "net_tax_payable": calc.round_off_decimal(net_tax_payable_old),
            "balance_tax_to_be_paid": calc.round_off_decimal(balance_tax_to_be_paid_old),
            "interest_u_s_234a_b_c": calc.round_off_decimal(total_interest_234_old),
            "penalt_u_s_234f": calc.round_off_decimal(penalty_us_234F_old),
            "tax_payable": calc.round_off_decimal(tax_payable_old),
        }
    }

        pdf = self.render_to_pdf('itr_computations_old_regime_report.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"{slugify(tax_return.user.username)}-old-regime-computation.pdf"
            content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response

        return HttpResponse


class IncometaxComputationsNewPdfView(generics.GenericAPIView, GeneratePdfMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        encoded_income_tax_return_id = self.kwargs['income_tax_return_id']
        income_tax_return_id = AlphaId.decode(encoded_income_tax_return_id)

        try:
            tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=request.user)
        except IncomeTaxReturn.DoesNotExist:
            return HttpResponse("Invalid Income Tax Return ID or Unauthorized access.", status=404)

        calc = IncomeTaxCalculations()
        base_standard_deduction = Decimal('50000')

        salary_incomes = tax_return.salary_incomes.all()
        rental_incomes = tax_return.rental_incomes.all()
        capital_gains = tax_return.capital_gains.all()
        business_incomes = tax_return.business_income.all()
        interest_incomes = tax_return.exempt_incomes.all()
        dividend_incomes = tax_return.dividend_income.all()
        exempt_incomes = tax_return.exempt_incomes_agriculture.all()
        agriculture_incomes = tax_return.agriculture_income.all()

        salary_incomes_data_new, _, total_income_from_salaries_new, _ = calc.calculate_salary_income(salary_incomes, base_standard_deduction)
        rental_incomes_data, total_rental_income_new, _ = calc.calculate_rental_income(rental_incomes)
        total_capital_gains_income, long_term_capital_gains_112A, long_term_capital_gains_others, short_term_capital_gains = calc.calculate_capital_gains(capital_gains)
        business_incomes_data, total_income_from_business = calc.calculate_business_income(business_incomes)
        total_interest_income = sum([i.interest_amount for i in interest_incomes])
        total_dividend_income = sum([d.amount for d in dividend_incomes])
        total_winnings_income = 0  # Assuming you handle this elsewhere
        total_exempt_income = sum([e.amount for e in exempt_incomes])
        total_net_income_from_agriculture = sum([agri_income.net_income for agri_income in agriculture_incomes])
        total_combined_exempt_income = total_exempt_income + total_net_income_from_agriculture

        deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum = calc.calculate_deductions(tax_return.deductions, interest_incomes)
        total_deduction_amount = deduction_80c_sum + nps_contribution_sum + medical_premium_sum + interest_on_savings_sum

        total_tds_or_tcs, total_self_assessment_tax, total_advance_tax = calc.calculate_tds_advance_tax(tax_return.tds_or_tcs_deduction.all(), tax_return.self_assesment_and_advance_tax_paid.all(), tax_return.income_tax_return_year.start_date, tax_return.income_tax_return_year.end_date)
        gross_total_income_new = calc.calculate_gross_total_income(total_income_from_salaries_new, total_rental_income_new, total_income_from_business, total_capital_gains_income, total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income)
        total_income_new = gross_total_income_new - total_deduction_amount
        tax_liability_new = calc.calculate_tax_liability_new_regime(gross_total_income_new)
        surcharge_new = calc.calculate_surcharge(gross_total_income_new, tax_liability_new, regime="new")
        tax_rebate_new = calc.calculate_tax_rebate_new_regime(gross_total_income_new, tax_liability_new)
        cess_new = calc.calculate_cess(tax_liability_new, surcharge_new, tax_rebate_new)
        net_tax_payable_new = tax_liability_new + surcharge_new - tax_rebate_new + cess_new
        balance_tax_to_be_paid_new = net_tax_payable_new - total_advance_tax - total_tds_or_tcs
        total_interest_234_new = calc.calculate_interest_234A(balance_tax_to_be_paid_new, timezone.now().date(), tax_return.income_tax_return_year.due_date) + \
                                 calc.calculate_interest_234B(balance_tax_to_be_paid_new, total_advance_tax, net_tax_payable_new) + \
                                 calc.calculate_interest_234C(balance_tax_to_be_paid_new, total_advance_tax, net_tax_payable_new)
        penalty_us_234F_new = calc.calculate_penalty_us_234F(total_income_new, timezone.now().date(), tax_return.income_tax_return_year.due_date)
        tax_payable_new = balance_tax_to_be_paid_new + total_interest_234_new + penalty_us_234F_new

        context = {
            "new_regime_data": {
                "salary_incomes": salary_incomes_data_new,
                "total_income_from_salaries": calc.round_off_decimal(total_income_from_salaries_new),
                "rental_incomes": rental_incomes_data,
                "long_term_capital_gain_u_s_112a": calc.round_off_decimal(long_term_capital_gains_112A),
                "long_term_capital_gain_others": calc.round_off_decimal(long_term_capital_gains_others),
                "short_term_capital_gain": calc.round_off_decimal(short_term_capital_gains),
                "total_capital_gains_income": calc.round_off_decimal(total_capital_gains_income),
                "business_incomes": business_incomes_data,
                "total_income_from_business": calc.round_off_decimal(total_income_from_business),
                "interest_income": calc.round_off_decimal(total_interest_income),
                "dividend_income": calc.round_off_decimal(total_dividend_income),
                "winnings_lotteries_games_bettings": calc.round_off_decimal(total_winnings_income),
                "total_of_other_incomes": calc.round_off_decimal(total_interest_income + total_dividend_income + total_winnings_income),
                "exempt_income": calc.round_off_decimal(total_exempt_income),
                "net_income_from_agriculture": calc.round_off_decimal(total_net_income_from_agriculture),
                "total_exempt_income": calc.round_off_decimal(total_combined_exempt_income),
                "deduction_u_s_80c": calc.round_off_decimal(deduction_80c_sum),
                "nps_contribution_u_s_ccd": calc.round_off_decimal(nps_contribution_sum),
                "80d_medical_insurance_premium": calc.round_off_decimal(medical_premium_sum),
                "80tta_interest_on_savings_acc": calc.round_off_decimal(interest_on_savings_sum),
                "total_deduction_amount": calc.round_off_decimal(total_deduction_amount),
                "tds_or_tcs": calc.round_off_decimal(total_tds_or_tcs),
                "self_assessment_tax": calc.round_off_decimal(total_self_assessment_tax),
                "advance_tax": calc.round_off_decimal(total_advance_tax),
                "gross_total_income": calc.round_off_decimal(gross_total_income_new),
                "total_income": calc.round_off_decimal(total_income_new),
                "tax_liability_at_normal_rates": calc.round_off_decimal(tax_liability_new),
                "tax_rebate": calc.round_off_decimal(tax_rebate_new),
                "surcharge": calc.round_off_decimal(surcharge_new),
                "cess": calc.round_off_decimal(cess_new),
                "net_tax_payable": calc.round_off_decimal(net_tax_payable_new),
                "balance_tax_to_be_paid": calc.round_off_decimal(balance_tax_to_be_paid_new),
                "interest_u_s_234a_b_c": calc.round_off_decimal(total_interest_234_new),
                "penalt_u_s_234f": calc.round_off_decimal(penalty_us_234F_new),
                "tax_payable": calc.round_off_decimal(tax_payable_new),
            }
        }

        pdf = self.render_to_pdf('itr_computations_new_regime_report.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"{slugify(tax_return.user.username)}-new-regime-computation.pdf"
            content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response

        return HttpResponse


