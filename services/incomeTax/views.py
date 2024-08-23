import json
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxReturn, IncomeTaxReturnYears, \
    ResidentialStatusQuestions, IncomeTaxBankDetails, IncomeTaxAddress, SalaryIncome, RentalIncome, BuyerDetails, \
    CapitalGains, BusinessIncome, AgricultureIncome, LandDetails, InterestIncome, InterestOnItRefunds, DividendIncome, \
    IncomeFromBetting, TdsOrTcsDeduction, SelfAssesmentAndAdvanceTaxPaid, Deductions, ExemptIncome
from services.incomeTax.serializers import IncomeTaxProfileSerializer, \
    IncomeTaxReturnSerializer, ResidentialStatusQuestionsSerializer, SalaryIncomeSerializer, RentalIncomeSerializer, \
    CapitalGainsSerializer, BusinessIncomeSerializer, AgricultureIncomeSerializer, InterestIncomeSerializer, \
    InterestOnItRefundsSerializer, DividendIncomeSerializer, IncomeFromBettingSerializer, TdsOrTcsDeductionSerializer, \
    SelfAssesmentAndAdvanceTaxPaidSerializer, DeductionsSerializer, ExemptIncomeSerializer, BuyerDetailsSerializer, \
    LandDetailsSerializer, AgricultureAndExemptIncomeSerializer, OtherIncomesSerializer, TaxPaidSerializer, \
    TdsPdfSerializer, ChallanPdfUploadSerializer, AISPdfUploadSerializer
from services.incomeTax.services import PanVerificationService
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
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
        try:
            income_tax_profile = IncomeTaxProfile.objects.get(user=user)
            pan_no = income_tax_profile.pan_no
        except IncomeTaxProfile.DoesNotExist:
            return Response({'status': 'error', 'message': 'Income Tax Profile does not exist for the user'},
                            status=status.HTTP_404_NOT_FOUND)
        income_tax_profile, created = IncomeTaxProfile.objects.update_or_create(
            user=user,
            defaults={
                'first_name': user.first_name,
                'middle_name': '',
                'last_name': user.last_name,
                'date_of_birth': '2024-01-01',
                'fathers_name': 'Father Beyondtax',
                'gender': IncomeTaxProfile.MALE,
                'marital_status': IncomeTaxProfile.Married,
                'aadhar_no': '123456789012',
                'aadhar_enrollment_no': '123456789012345678901234',
                'pan_no': pan_no,
                'mobile_number': "9654327863",
                'email': user.email,
                'residential_status': IncomeTaxProfile.IndianResident,
                'is_data_imported': True
            }
        )
        IncomeTaxBankDetails.objects.update_or_create(
            income_tax=income_tax_profile,
            defaults={
                'account_no': '1234567890',
                'ifsc_code': 'IFSC0001234',
                'bank_name': 'Bank of Example',
                'type': IncomeTaxBankDetails.SavingsAccount
            }
        )
        IncomeTaxAddress.objects.update_or_create(
            income_tax=income_tax_profile,
            defaults={
                'door_no': '123',
                'permise_name': 'Premise Name',
                'street': 'Street Name',
                'area': 'Area Name',
                'city': 'City Name',
                'state': 'State Name',
                'pincode': '123456',
                'country': 'Country Name'
            }
        )
        if created:
            message = 'Tax profile data created successfully'
        else:
            message = 'Tax profile data updated successfully'

        return Response({'status': 'success', 'message': message, 'is_data_imported': True}, status=status.HTTP_201_CREATED)


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
            item['income_tax'] = income_tax_profile.id
            item['income_tax_return'] = income_tax_return.id
            item.pop('id', None)

            agriculture_serializer = AgricultureIncomeSerializer(data=item)
            agriculture_serializer.is_valid(raise_exception=True)
            agriculture_income = agriculture_serializer.save()
            agriculture_incomes_created.append(agriculture_serializer.data)

            for land in land_data:
                land['agriculture_income'] = agriculture_income.id
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
            item['income_tax'] = income_tax_profile.id
            item['income_tax_return'] = income_tax_return.id
            item.pop('id', None)
            exempt_serializer = ExemptIncomeSerializer(data=item)
            exempt_serializer.is_valid(raise_exception=True)
            exempt_income = exempt_serializer.save()
            exempt_incomes_created.append(exempt_serializer.data)
        created_records['exempt_incomes'] = exempt_incomes_created
        return Response({'status': 'success', 'message': 'Incomes created successfully', 'data': created_records},
                        status=status.HTTP_201_CREATED)

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
            if 'id' in item:
                item['id'] = AlphaId.decode(item['id'])

            land_data = item.pop('land_details', [])
            agriculture_income, created = AgricultureIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            land_ids = []
            for land in land_data:
                if 'id' in land:
                    land['id'] = AlphaId.decode(land['id'])
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
            if 'id' in item:
                item['id'] = AlphaId.decode(item['id'])

            exempt_income, created = ExemptIncome.objects.update_or_create(
                income_tax=income_tax_profile,
                income_tax_return=income_tax_return,
                id=item.get('id'),
                defaults=item
            )
            exempt_incomes_updated.append(ExemptIncomeSerializer(exempt_income).data)
        updated_records['exempt_incomes'] = exempt_incomes_updated
        return Response({'status': 'success', 'message': 'Incomes updated successfully', 'data': updated_records},
                        status=status.HTTP_200_OK)


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