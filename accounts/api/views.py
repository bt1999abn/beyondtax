from allauth.socialaccount.models import SocialApp, SocialToken, SocialLogin
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import login, get_user_model
from django.core.files.images import get_image_dimensions
from django.db.models import Sum
from knox.models import AuthToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers, generics, request
from django.utils import timezone
from datetime import timedelta
from knox import views as knox_views
from accounts.api.serializers import RegistrationSerializer, UserProfileSerializer, WorkOrderSerializer, \
    ChangePasswordSerializer, WorkOrderDownloadDocumentSerializer, \
    UserBasicDetailsSerializer, WorkOrderDownloadDocumentListSerializer, WorkorderPaymentSerializer, \
    UpcomingDueDateSerializer, WorkOrderDocumentsUploadSerializer
from rest_framework.generics import CreateAPIView, ListAPIView
from accounts.api.serializers import LoginSerializer
from accounts.models import OtpRecord, WorkOrder, WorkOrderDownloadDocument, WorkorderPayment, \
    UpcomingDueDates
from accounts.services import SendMobileOtpService
from shared.rest.pagination import CustomPagination


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


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)

        social_app = SocialApp.objects.get(provider='google')
        token = SocialToken(app=social_app, token=code)
        login = SocialLogin(token=token)

        try:
            login.lookup()
            login.save(request, connect=True)
            user = login.account.user
            user.is_active = True
            user.save()
            _, login_token = AuthToken.objects.create(user)
            return Response({'token': login_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return WorkOrder.objects.filter(user=user)


class WorkOrderDocumentUploadAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        try:
            work_order_id = request.data['work_order_id']
            work_order = WorkOrder.objects.get(id=work_order_id)
        except (KeyError, WorkOrder.DoesNotExist):
            return Response({"error": "Work order with the provided ID does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)
        documents = []
        for key, file in request.FILES.items():
            if key.startswith('documents['):
                index = key.split('[')[1].split(']')[0]
                document_name_key = f'documents[{index}].document_name'
                if document_name_key in request.data:
                    documents.append({
                        'document_name': request.data[document_name_key],
                        'document_file': file
                    })

        data = {
            'work_order_id': work_order_id,
            'documents': documents
        }

        serializer = WorkOrderDocumentsUploadSerializer(data=data, context={'work_order': work_order,
                                                                            'uploaded_by_beyondtax': False})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Documents uploaded successfully"}, status=status.HTTP_201_CREATED)


class WorkOrderDocumentUploadByBeyondtaxAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        try:
            work_order_id = request.data['work_order_id']
            work_order = WorkOrder.objects.get(id=work_order_id)
        except (KeyError, WorkOrder.DoesNotExist):
            return Response({"error": "Work order with the provided ID does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        documents = []
        for key, file in request.FILES.items():
            if key.startswith('documents['):
                index = key.split('[')[1].split(']')[0]
                document_name_key = f'documents[{index}].document_name'
                if document_name_key in request.data:
                    documents.append({
                        'document_name': request.data[document_name_key],
                        'document_file': file
                    })
        data = {
            'work_order_id': work_order_id,
            'documents': documents
        }
        serializer = WorkOrderDocumentsUploadSerializer(data=data, context={'work_order': work_order,
                                                                            'uploaded_by_beyondtax': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Documents uploaded successfully"}, status=status.HTTP_201_CREATED)


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request,*args,**kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response({"messages":"password updated succesfully"}, status= status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkOrderDocumentApi(ListAPIView):
    serializer_class = WorkOrderDownloadDocumentSerializer
    permission_classes = (IsAuthenticated,)


class WorkOrderStatusSummaryApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,*args,**kwargs):
        user = request.user
        user_workorders = WorkOrder.objects.filter(user=user)
        inprocess_count = user_workorders.filter(status=1).count()
        download_count = user_workorders.filter(status=2).count()
        total_amount_paid = user_workorders.aggregate(Sum('amount_paid'))
        data = {
            "inprocess_count": inprocess_count,
            "download_count": download_count,
            "total_amount_paid": total_amount_paid if total_amount_paid else 0
        }
        return Response(data, status=status.HTTP_200_OK)


class UserBasicDetailsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserBasicDetailsSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkOrderDownloadDocumentApi(generics.RetrieveAPIView):
    serializer_class = WorkOrderDownloadDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self,*args,**kwargs):
        work_order_id = self.kwargs.get('work_order_id')
        if not work_order_id:
            raise ValueError("WorkOrder ID is required.")
        try:
            document = WorkOrderDownloadDocument.objects.get(work_order_id=work_order_id)
            return document
        except WorkOrderDownloadDocument.DoesNotExist:
            raise serializers.ValidationError(f"No document found for WorkOrder ID {work_order_id}.")


class WorkOrderDownloadDocumentListApi(generics.ListAPIView):
    serializer_class = WorkOrderDownloadDocumentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return WorkOrderDownloadDocument.objects.filter(work_order__user=user, work_order__status=5)


class WorkorderPaymentRetriveApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, work_order_id):
        try:
            work_order = WorkOrder.objects.get(id=work_order_id)
        except WorkOrder.DoesNotExist:
            return Response({"error": f"No WorkOrder found with ID {work_order_id}"}, status=status.HTTP_404_NOT_FOUND)
        payments = WorkorderPayment.objects.filter(work_order=work_order)
        if not payments.exists():
            return Response({"error": f"No payments found for WorkOrder ID {work_order_id}"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = WorkorderPaymentSerializer(payments, many=True)

        return Response(serializer.data)


class UpcomingDueDatesApi(generics.ListAPIView):
    queryset = UpcomingDueDates.objects.all()
    serializer_class = UpcomingDueDateSerializer
