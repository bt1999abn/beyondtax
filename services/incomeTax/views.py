from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxReturn, IncomeTaxReturnYears, \
    ResidentialStatusQuestions, IncomeTaxBankDetails, IncomeTaxAddress, SalaryIncome, RentalIncome, BuyerDetails, \
    CapitalGains, BusinessIncome, AgricultureIncome, LandDetails, InterestIncome, InterestOnItRefunds, DividendIncome, \
    IncomeFromBetting, TdsOrTcsDeduction, SelfAssesmentAndAdvanceTaxPaid, Deductions, ExemptIncome
from services.incomeTax.serializers import IncomeTaxProfileSerializer, \
    IncomeTaxReturnSerializer, ResidentialStatusQuestionsSerializer, SalaryIncomeSerializer, RentalIncomeSerializer, \
    CapitalGainsSerializer, BusinessIncomeSerializer, AgricultureIncomeSerializer, InterestIncomeSerializer, \
    InterestOnItRefundsSerializer, DividendIncomeSerializer, IncomeFromBettingSerializer, TdsOrTcsDeductionSerializer, \
    SelfAssesmentAndAdvanceTaxPaidSerializer, DeductionsSerializer, ExemptIncomeSerializer
from services.incomeTax.services import PanVerificationService


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
            profile, next_question_data = profile_serializer.save()
            response_serializer = IncomeTaxProfileSerializer(profile, context={'request': request})
            response_data = response_serializer.data
            response_data['next_question'] = next_question_data

            if next_question_data and "id" in next_question_data:
                return Response({
                    "status_code": 200,
                    "status_text": "OK",
                    "data": response_data
                }, status=status.HTTP_200_OK)

            return Response({
                "status_code": 201,
                "status_text": "Created",
                "data": response_data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status_code": 400,
            "status_text": "Bad Request",
            "errors": profile_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            profile = IncomeTaxProfile.objects.get(user=request.user)
        except IncomeTaxProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = IncomeTaxProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
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
        pan_number = request.data.get('pan_number')

        try:
            tax_profile = IncomeTaxProfile.objects.get(pan_no=pan_number)
            user = tax_profile.user

            if not user.email:
                return Response({'status': 'error', 'message': 'No email associated with this PAN number'},
                                status=status.HTTP_400_BAD_REQUEST)

            pan_service = PanVerificationService()
            otp_id = pan_service.send_pan_verification_otp(user, pan_number)
            return Response({'status': 'success', 'message': 'OTP sent to your email', 'otp_id': otp_id},
                            status=status.HTTP_200_OK)

        except IncomeTaxProfile.DoesNotExist:
            return Response({'status': 'error', 'message': 'User with this PAN number does not exist'},
                            status=status.HTTP_404_NOT_FOUND)


class VerifyPanOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        otp_id = request.data.get('otp_id')
        otp = request.data.get('otp')
        if not otp:
            return Response({'status': 'error', 'message': 'OTP is a required field'}, status=status.HTTP_400_BAD_REQUEST)

        pan_service = PanVerificationService()
        if pan_service.verify_pan_otp(otp_id, otp):
            user = request.user
            income_tax_profile = user.income_tax_profile
            if income_tax_profile:
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
                    'name': year.name
                })

            return Response({
                'status_code': 200,
                'status_text': 'OK',
                'data': {
                    'status': 'success',
                    'message': 'PAN OTP verification successful and tax return record created',
                    'is_pan_verified': income_tax_profile.is_pan_verified
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'message': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)


class ImportIncomeTaxProfileDataApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        income_tax_profile, created = IncomeTaxProfile.objects.update_or_create(
            user=user,
            defaults={
                'first_name': 'beyond',
                'middle_name': 't',
                'last_name': 'Tax',
                'date_of_birth': '2024-01-01',
                'fathers_name': 'Father Beyondtax',
                'gender': IncomeTaxProfile.MALE,
                'marital_status': IncomeTaxProfile.Married,
                'aadhar_no': '123456789012',
                'aadhar_enrollment_no': '123456789012345678901234',
                'pan_no': 'ABCDE1234F',
                'mobile_number': '9876543210',
                'email': 'johndoe@example.com',
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

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return SalaryIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class SalaryIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SalaryIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                salary_income, created = SalaryIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(salary_income.id)

            SalaryIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Salary incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of salary incomes'}, status=status.HTTP_400_BAD_REQUEST)


class RentalIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentalIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return RentalIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class RentalIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentalIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                rental_income, created = RentalIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(rental_income.id)
            RentalIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Rental incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of rental incomes'}, status=status.HTTP_400_BAD_REQUEST)


class CapitalGainsListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CapitalGainsSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return CapitalGains.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class CapitalGainsUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CapitalGainsSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                buyers_data = item.pop('buyer_details', [])
                capital_gain, created = CapitalGains.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(capital_gain.id)

                buyer_ids = []
                for buyer in buyers_data:
                    buyer_detail, buyer_created = BuyerDetails.objects.update_or_create(
                        capital_gains=capital_gain,
                        id=buyer.get('id'),
                        defaults=buyer
                    )
                    buyer_ids.append(buyer_detail.id)
                BuyerDetails.objects.filter(capital_gains=capital_gain).exclude(id__in=buyer_ids).delete()
            CapitalGains.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Capital gains and buyer details updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of capital gains'}, status=status.HTTP_400_BAD_REQUEST)


class BusinessIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return BusinessIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class BusinessIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)

        data = request.data

        if isinstance(data, list):
            updated_ids = []
            for item in data:
                business_income, created = BusinessIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(business_income.id)
            BusinessIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Business incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of business incomes'}, status=status.HTTP_400_BAD_REQUEST)


class AgricultureIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AgricultureIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return AgricultureIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class AgricultureIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AgricultureIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                land_data = item.pop('land_details', [])
                agriculture_income, created = AgricultureIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(agriculture_income.id)

                land_ids = []
                for land in land_data:
                    land_detail, land_created = LandDetails.objects.update_or_create(
                        agriculture_income=agriculture_income,
                        id=land.get('id'),
                        defaults=land
                    )
                    land_ids.append(land_detail.id)
                LandDetails.objects.filter(agriculture_income=agriculture_income).exclude(id__in=land_ids).delete()
            AgricultureIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Agriculture incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of agriculture incomes'}, status=status.HTTP_400_BAD_REQUEST)


class ExemptIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExemptIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return ExemptIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class ExemptIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExemptIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                exempt_income, created = ExemptIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(exempt_income.id)
            ExemptIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Exempt incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of exempt incomes'}, status=status.HTTP_400_BAD_REQUEST)


class InterestIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InterestIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return InterestIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class InterestIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InterestIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                interest_income, created = InterestIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(interest_income.id)
            InterestIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Interest incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of interest incomes'}, status=status.HTTP_400_BAD_REQUEST)


class InterestOnItRefundsListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InterestOnItRefundsSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return InterestOnItRefunds.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class InterestOnItRefundsUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InterestOnItRefundsSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                interest_on_it_refund, created = InterestOnItRefunds.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(interest_on_it_refund.id)
            InterestOnItRefunds.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Interest on IT refunds updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of interest on IT refunds'}, status=status.HTTP_400_BAD_REQUEST)


class DividendIncomeListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DividendIncomeSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return DividendIncome.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class DividendIncomeUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DividendIncomeSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                dividend_income, created = DividendIncome.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(dividend_income.id)
            DividendIncome.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Dividend incomes updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of dividend incomes'}, status=status.HTTP_400_BAD_REQUEST)


class IncomeFromBettingListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IncomeFromBettingSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return IncomeFromBetting.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class IncomeFromBettingUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IncomeFromBettingSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                income_from_betting, created = IncomeFromBetting.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(income_from_betting.id)
            IncomeFromBetting.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'Income from betting updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of income from betting'}, status=status.HTTP_400_BAD_REQUEST)


class TdsOrTcsDeductionListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TdsOrTcsDeductionSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return TdsOrTcsDeduction.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class TdsOrTcsDeductionUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TdsOrTcsDeductionSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                tds_or_tcs_deduction, created = TdsOrTcsDeduction.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(tds_or_tcs_deduction.id)
            TdsOrTcsDeduction.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()
            return Response({'status': 'success', 'message': 'TDS or TCS deductions updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of TDS or TCS deductions'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': message, 'is_data_imported': True}, status=status.HTTP_201_CREATED)


class SelfAssesmentAndAdvanceTaxPaidListCreateApi(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SelfAssesmentAndAdvanceTaxPaidSerializer

    def get_queryset(self):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        return SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax__user=user, income_tax_return_id=income_tax_return_id)

    def perform_create(self, serializer):
        user = self.request.user
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        serializer.save(income_tax=income_tax_profile, income_tax_return=income_tax_return)


class SelfAssesmentAndAdvanceTaxPaidUpdateApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SelfAssesmentAndAdvanceTaxPaidSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        income_tax_return = IncomeTaxReturn.objects.get(id=income_tax_return_id, user=user)
        data = request.data
        if isinstance(data, list):
            updated_ids = []
            for item in data:
                self_assessment_and_advance_tax_paid, created = SelfAssesmentAndAdvanceTaxPaid.objects.update_or_create(
                    income_tax=income_tax_profile,
                    income_tax_return=income_tax_return,
                    id=item.get('id'),
                    defaults=item
                )
                updated_ids.append(self_assessment_and_advance_tax_paid.id)
            SelfAssesmentAndAdvanceTaxPaid.objects.filter(income_tax=income_tax_profile, income_tax_return=income_tax_return).exclude(id__in=updated_ids).delete()

            return Response({'status': 'success', 'message': 'Self-assessment and advance tax paid updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failure', 'message': 'Invalid data format, expected a list of self-assessment and advance tax paid'}, status=status.HTTP_400_BAD_REQUEST)


class DeductionsApi(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeductionsSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
        try:
            deductions = Deductions.objects.get(income_tax__user=user, income_tax_return_id=income_tax_return_id)
            serializer = DeductionsSerializer(deductions)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Deductions.DoesNotExist:
            return Response({'status': 'failure', 'message': 'Deductions not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        income_tax_return_id = self.request.query_params.get('income_tax_return_id')
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