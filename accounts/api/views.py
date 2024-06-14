from django.contrib.auth import login, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.images import get_image_dimensions
from django.shortcuts import redirect
from django_filters.rest_framework import filters, DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers, generics, parsers
from django.utils import timezone
from datetime import timedelta
from knox import views as knox_views
from accounts.api.serializers import RegistrationSerializer, UserProfileSerializer, \
    ChangePasswordSerializer, UserBasicDetailsSerializer, UpcomingDueDateSerializer, AuthSerializer, \
    BusinessContactPersonSerializer, UserBusinessContactPersonsSerializer, UpcomingDueDatesFilter, \
    PasswordResetSerializer
from accounts.api.serializers import LoginSerializer
from accounts.models import OtpRecord, UpcomingDueDates, User, BusinessContactPersonDetails
from accounts.services import SendMobileOtpService, get_user_data, SendEmailOtpService, EmailService
from beyondTax import settings


class sendOtpApi(APIView):
    def post(self, request, *args, **kwargs):
        mobile_number = request.data.get('mobile_number')

        if not mobile_number:
            return Response({"error": "Mobile number is required"}, status=status.HTTP_400_BAD_REQUEST)

        service = SendMobileOtpService()
        success, otp_session_id = service.send_otp(phone_number=mobile_number)
        if success:
            return Response({
                "message": "OTP sent successfully.",
                "otp_session_id": otp_session_id
            })
        else:
            return Response({"error": "Something went wrong. Please try again."}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(knox_views.LoginView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            login(request, user)
            response = super().post(request, format=None)
            return Response(response.data, status=status.HTTP_200_OK)
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginApi(knox_views.LoginView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        auth_serializer = AuthSerializer(data=request.GET)
        auth_serializer.is_valid(raise_exception=True)
        validate_data = auth_serializer.validated_data
        user_data = get_user_data(validate_data)
        user = User.objects.get(email=user_data['email'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        response = super().post(request, format=None)
        FE_SIGNIN_SUCCESS_URL = settings.FE_GOOGLE_LOGIN_SUCCESS.format(token=response.data["token"])
        return redirect(FE_SIGNIN_SUCCESS_URL)


class RegistrationApiView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # print(user.mobile_number)
            # service = SendMobileOtpService()
            # success, result = service.send_otp(phone_number=user.mobile_number)
            # if success:
            return Response({
                    'user_id': user.id,
                    # 'otp_session_id': result
                }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtpApiView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        otp_session_id = request.data.get('otp_session_id')
        otp_provided = request.data.get('otp')
        otp_record = OtpRecord.objects.filter(otp_session_id=otp_session_id).first()
        User = get_user_model()
        OTP_EXPIRY = 3  # minutes

        if not otp_record:
            raise serializers.ValidationError("Please send the OTP first.")

        if timezone.now() > otp_record.created_at + timedelta(minutes=OTP_EXPIRY):
            raise serializers.ValidationError("OTP has expired.")

        if otp_record.otp != otp_provided:
            raise serializers.ValidationError("Wrong OTP.")
        user = User.objects.get(mobile_number=otp_record.mobile_number)
        if user:
            user.is_active = True
            user.save()
            return Response({"message": "OTP verified and user registered successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class ProfileApiView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = RegistrationSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateProfileApi(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                try:
                    width, height = get_image_dimensions(profile_picture)
                    if not width or not height:
                        return Response({"profile_picture": ["Invalid image, could not get dimensions."]},
                                        status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"profile_picture": ["Invalid image, error: " + str(e)]},
                                    status=status.HTTP_400_BAD_REQUEST)

                user.profile_picture = profile_picture
                user.save()

            serializer.save()
            return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request,*args,**kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response({"messages":"password updated succesfully"}, status= status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBasicDetailsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserBasicDetailsSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpcomingDueDatesApi(generics.ListAPIView):
    queryset = UpcomingDueDates.objects.all()
    serializer_class = UpcomingDueDateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UpcomingDueDatesFilter


class SendEmailOtpApi(APIView):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            otp_service = SendEmailOtpService()
            otp_session_id = otp_service.send_otp(user)
            return Response({'status': 'success', 'message': 'OTP sent to your email', 'otp_session_id': otp_session_id}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)


class VerifyEmailOtpApi(APIView):
    def post(self, request, *args, **kwargs):
        otp_session_id = request.data.get('otp_session_id')
        otp = request.data.get('otp')
        if not otp:
            return Response({'status': 'error', 'message': 'OTP is a required field'},
                            status=status.HTTP_400_BAD_REQUEST)
        otp_service = SendEmailOtpService()
        if otp_service.verify_otp(otp_session_id, otp):
            return Response({'status': 'success', 'message': 'OTP verification successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'message': 'Invalid or expired OTP'},
                            status=status.HTTP_400_BAD_REQUEST)


class SendEmailApi(APIView):
    def post(self, request, *args, **kwargs):
        recipient_email = request.data.get('recipient_email')
        subject = request.data.get('subject')
        template_path = 'email_templates/message_email.html'

        context = {
            'recipient_name': request.data.get('recipient_name', ''),
            'message': 'you can login to your beyondtax profile with your new password',
            'subject': 'password hasbeen successfully changed',
        }
        if not recipient_email:
            return Response({'status': 'error', 'message': 'Recipient email is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        email_service = EmailService()
        email_service.send_email(recipient_email,subject, template_path, context)

        return Response({'status': 'success', 'message': 'Email sent successfully'}, status=status.HTTP_200_OK)


class BusinessContactPersonAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.client_type == User.Individual:
            return Response([])
        else:
            contact_persons = BusinessContactPersonDetails.objects.filter(user=user)
            serializer = BusinessContactPersonSerializer(contact_persons, many=True)
            return Response(serializer.data)

    def post(self, request):
        if request.user.client_type == User.Individual:
            return Response({"detail": "Individuals cannot have contact persons"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserBusinessContactPersonsSerializer(data=request.data)
        if serializer.is_valid():
            contact_persons_data = serializer.validated_data['contact_persons']
            contact_persons = []
            for contact_person_data in contact_persons_data:
                contact_person = BusinessContactPersonDetails.objects.create(
                    user=request.user,
                    **contact_person_data
                )
                contact_persons.append(contact_person)
            return Response(
                {
                    "message": "Contact persons created successfully",
                    "contact_persons": BusinessContactPersonSerializer(contact_persons, many=True).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            contact_person = BusinessContactPersonDetails.objects.get(pk=pk, user=request.user)
        except BusinessContactPersonDetails.DoesNotExist:
            return Response({"detail": "Contact person not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BusinessContactPersonSerializer(contact_person, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordApi(APIView):

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            otp_session_id = serializer.validated_data['otp_session_id']
            password = serializer.validated_data['password']

            try:
                otp_record = OtpRecord.objects.get(otp_session_id=otp_session_id)
                user = User.objects.get(email=otp_record.email)
                user.password = make_password(password)
                user.save()
                otp_record.delete()
                return Response({'status': 'success', 'message': 'Password reset successfully'},
                                status=status.HTTP_200_OK)
            except OtpRecord.DoesNotExist:
                return Response({'status': 'error', 'message': 'Invalid OTP session ID'},
                                status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'status': 'error', 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)