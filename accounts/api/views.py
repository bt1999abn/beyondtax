from django.contrib.auth import login, get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils import timezone
from datetime import timedelta
from knox import views as knox_views
from accounts.api.serializers import RegistrationSerializer, UserProfileSerializer, WorkOrderSerializer, \
    WorkOrderFilesSerializer, ChangePasswordSerializer
from rest_framework.generics import CreateAPIView, ListAPIView
from accounts.api.serializers import LoginSerializer
from accounts.models import OtpRecord, WorkOrder, ServicePages
from accounts.services import SendMobileOtpService


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
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response.data, status=status.HTTP_200_OK)


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

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkOrderApiView(APIView):

    permission_classes = (IsAuthenticated,)


class WorkOrderApi(CreateAPIView):
    serializer_class = WorkOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetWorkOrderApi(ListAPIView):
    serializer_class = WorkOrderSerializer

    def get_queryset(self):
        user = self.request.user
        return WorkOrder.objects.filter(user=user)


class WorkOrderFileUploadAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,*args,**kwargs):
        serializer = WorkOrderFilesSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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








