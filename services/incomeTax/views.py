from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxReturn, IncomeTaxReturnYears, \
    ResidentialStatusQuestions, IncomeTaxBankDetails, IncomeTaxAddress
from services.incomeTax.serializers import IncomeTaxProfileSerializer, \
    IncomeTaxReturnSerializer, ResidentialStatusQuestionsSerializer
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
            'data': response_data
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

        # Create IncomeTaxProfile
        income_tax_profile = IncomeTaxProfile.objects.create(
            user=user,
            first_name='beyond',
            middle_name='t',
            last_name='Tax',
            date_of_birth='2024-01-01',
            fathers_name='Father Beyondtax',
            gender=IncomeTaxProfile.MALE,
            marital_status=IncomeTaxProfile.Married,
            aadhar_no='123456789012',
            aadhar_enrollment_no='123456789012345678901234',
            pan_no='ABCDE1234F',
            mobile_number='9876543210',
            email='johndoe@example.com',
            residential_status=IncomeTaxProfile.IndianResident
        )

        # Create IncomeTaxBankDetails
        IncomeTaxBankDetails.objects.create(
            income_tax=income_tax_profile,
            account_no='1234567890',
            ifsc_code='IFSC0001234',
            bank_name='Bank of Example',
            type=IncomeTaxBankDetails.SavingsAccount
        )

        # Create IncomeTaxAddress
        IncomeTaxAddress.objects.create(
            income_tax=income_tax_profile,
            door_no='123',
            permise_name='Premise Name',
            street='Street Name',
            area='Area Name',
            city='City Name',
            state='State Name',
            pincode='123456',
            country='Country Name'
        )

        return Response({'status': 'success', 'message': 'Tax profile data imported successfully'}, status=status.HTTP_201_CREATED)