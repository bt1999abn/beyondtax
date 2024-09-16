from collections import defaultdict, OrderedDict

from django.contrib.auth import login, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.images import get_image_dimensions
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers, generics, viewsets
from django.utils import timezone
from datetime import timedelta, date, datetime
from knox import views as knox_views
from accounts.api.serializers import RegistrationSerializer, UserProfileSerializer, \
    ChangePasswordSerializer, UserBasicDetailsSerializer, UpcomingDueDateSerializer, AuthSerializer, \
    BusinessContactPersonSerializer, UserBusinessContactPersonsSerializer, UpcomingDueDatesFilter, \
    PasswordResetSerializer, UpdateUserTypeSerializer, ProfileInformationSerializer, UserSerializer, \
    ProfileAddressSerializer, ProfileInformationUpdateSerializer, \
    ProfileBankDetailsSerializer, GovernmentIDSerializer, EmailUpdateOtpSerializer
from accounts.api.serializers import LoginSerializer
from accounts.models import OtpRecord, UpcomingDueDates, User, BusinessContactPersonDetails, ProfileInformation, \
    ProfileAddress, GovernmentID, ProfileBankAccounts
from accounts.services import SendMobileOtpService, get_user_data, SendEmailOtpService, EmailService
from beyondTax import settings
from shared.libs.hashing import AlphaId


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
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        response = super().post(request, format=None)
        response.data.update({
            'user': serializer.data['user']
        })
        return Response(response.data, status=status.HTTP_200_OK)


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
                    'user_id': AlphaId.encode(user.id),
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
        serializer = UserProfileSerializer(user)
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
            updated_user_data = UserProfileSerializer(user, context={'request': request}).data
            return Response({"message": "Profile updated successfully.", "data": updated_user_data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request,*args,**kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response({"messages":"password updated succesfully"}, status= status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBasicDetailsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserBasicDetailsSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpcomingDueDatesApi(generics.ListAPIView):
    serializer_class = UpcomingDueDateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UpcomingDueDatesFilter

    def get_queryset(self):
        today = date.today()
        first_day_of_month = today.replace(day=1)
        next_month = first_day_of_month + timedelta(days=32)
        last_day_of_month = next_month.replace(day=1) - timedelta(days=1)

        return UpcomingDueDates.objects.filter(
            date__gte=first_day_of_month,
            date__lte=last_day_of_month
        )


class UpcomingDueDatesByMonthApi(generics.ListAPIView):
    serializer_class = UpcomingDueDateSerializer

    def get_queryset(self):
        return UpcomingDueDates.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        grouped_by_month = defaultdict(list)

        for due_date in serializer.data:
            if 'formatted_date' in due_date:
                due_date_obj = datetime.strptime(due_date['formatted_date'], '%d-%m-%Y')
                month_key = due_date_obj.strftime('%B').lower()
                grouped_by_month[month_key].append(due_date)

        month_order = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]

        ordered_response = {}
        for month in month_order:
            if grouped_by_month[month]:
                ordered_response[month] = grouped_by_month[month]

        return Response(ordered_response, status=status.HTTP_200_OK)


class SendEmailOtpApi(APIView):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            otp_service = SendEmailOtpService()
            otp_id = otp_service.send_otp(user)
            return Response({'status': 'success', 'message': 'OTP sent to your email', 'otp_id': otp_id}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)


class VerifyEmailOtpApi(APIView):
    def post(self, request, *args, **kwargs):
        otp_id = request.data.get('otp_id')
        otp = request.data.get('otp')
        if not otp:
            return Response({'status': 'error', 'message': 'OTP is a required field'},
                            status=status.HTTP_400_BAD_REQUEST)

        otp_service = SendEmailOtpService()
        if otp_service.verify_otp(otp_id, otp):
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
            decoded_pk = AlphaId.decode(pk)
            contact_person = BusinessContactPersonDetails.objects.get(pk=decoded_pk, user=request.user)
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
            otp_id = serializer.validated_data['otp_id']
            password = serializer.validated_data['password']

            try:
                otp_record = OtpRecord.objects.get(id=otp_id)
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


class UpdateUserTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UpdateUserTypeSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'id': serializer.data['id'],
                'client_type': serializer.data['client_type'],
                'message': 'User type updated successfully'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            profile_info = ProfileInformation.objects.get(user=user)
        except ProfileInformation.DoesNotExist:
            profile_info = None

        profile_address = ProfileAddress.objects.filter(user=user)

        user_serializer = UserSerializer(user)
        profile_info_serializer = ProfileInformationSerializer(profile_info) if profile_info else None
        profile_address_serializer = ProfileAddressSerializer(profile_address, many=True)

        response_data = {
            'user': user_serializer.data,
            'profile_information': profile_info_serializer.data if profile_info_serializer else None,
            'profile_address': profile_address_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)


class ProfileInformationUpdateView(generics.UpdateAPIView):
    queryset = ProfileInformation.objects.all()
    serializer_class = ProfileInformationUpdateSerializer

    def get_object(self):
        return ProfileInformation.objects.get(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ProfileAddressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileAddressSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        user = request.user
        created_addresses = []
        errors = []

        address_keys = [key for key in request.data.keys() if key.startswith('addresses[')]
        num_addresses = max(
            [int(key.split('[')[1].split(']')[0]) for key in address_keys]) + 1

        for i in range(num_addresses):
            address_data = {
                'address_type': request.data.get(f"addresses[{i}].address_type"),
                'door_no': request.data.get(f"addresses[{i}].door_no"),
                'permise_name': request.data.get(f"addresses[{i}].permise_name"),
                'street': request.data.get(f"addresses[{i}].street"),
                'city': request.data.get(f"addresses[{i}].city"),
                'state': request.data.get(f"addresses[{i}].state"),
                'pincode': request.data.get(f"addresses[{i}].pincode"),
                'country': request.data.get(f"addresses[{i}].country"),
                'rent_status': request.data.get(f"addresses[{i}].rent_status"),
                'rental_agreement': request.FILES.get(f"addresses[{i}].rental_agreement")
            }
            if not any(value for key, value in address_data.items() if key != 'rental_agreement'):
                errors.append({
                    f"addresses[{i}]": "Some required fields are missing or have invalid data."
                })
                continue
            serializer = self.serializer_class(data=address_data)

            if serializer.is_valid():
                serializer.save(user=user)
                created_addresses.append(serializer.data)
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({
                "created_addresses": created_addresses,
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response({
            "created_addresses": created_addresses
        }, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        user = request.user
        updated_addresses = []
        errors = []
        address_keys = [key for key in request.data.keys() if key.startswith('addresses[')]
        num_addresses = max(
            [int(key.split('[')[1].split(']')[0]) for key in address_keys]) + 1

        for i in range(num_addresses):
            encoded_address_id = request.data.get(f"addresses[{i}].id")

            if not encoded_address_id:
                errors.append({"error": f"Address ID is required for updating address index {i}."})
                continue
            try:
                address_id = AlphaId.decode(encoded_address_id)
                address_instance = ProfileAddress.objects.get(id=address_id, user=user)
                address_data = {
                    'address_type': request.data.get(f"addresses[{i}].address_type"),
                    'door_no': request.data.get(f"addresses[{i}].door_no"),
                    'permise_name': request.data.get(f"addresses[{i}].permise_name"),
                    'street': request.data.get(f"addresses[{i}].street"),
                    'city': request.data.get(f"addresses[{i}].city"),
                    'state': request.data.get(f"addresses[{i}].state"),
                    'pincode': request.data.get(f"addresses[{i}].pincode"),
                    'country': request.data.get(f"addresses[{i}].country"),
                    'rent_status': request.data.get(f"addresses[{i}].rent_status"),
                    'rental_agreement': request.FILES.get(f"addresses[{i}].rental_agreement")
                }
                serializer = self.serializer_class(address_instance, data=address_data, partial=True)

                if serializer.is_valid():
                    updated_instance = serializer.save()
                    updated_instance_data = serializer.data
                    updated_instance_data['id'] = AlphaId.encode(updated_instance.id)
                    updated_addresses.append(updated_instance_data)
                else:
                    errors.append({encoded_address_id: serializer.errors})
            except ProfileAddress.DoesNotExist:
                errors.append({encoded_address_id: f"Address not found or does not belong to the user (index {i})."})
        if errors:
            return Response({
                "updated_addresses": updated_addresses,
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response({
            "updated_addresses": updated_addresses
        }, status=status.HTTP_200_OK)


class ProfileBankDetailsViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileBankDetailsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        return ProfileBankAccounts.objects.filter(user=user)

    def get_object(self):
        encoded_id = self.kwargs.get('pk')
        decoded_id = AlphaId.decode(encoded_id)
        queryset = self.get_queryset()
        return generics.get_object_or_404(queryset, pk=decoded_id)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response(
            {"message": "Bank account successfully deleted."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['put'], url_path='batch-update')
    def batch_update(self, request, *args, **kwargs):

        user = self.request.user
        data_list = request.data

        if not isinstance(data_list, list):
            raise ValidationError("Input data must be a list of bank accounts.")

        updated_instances = []
        for data in data_list:
            encoded_id = data.get('id')
            if not encoded_id:
                raise ValidationError("Each bank account must include an encoded 'id'.")

            decoded_id = AlphaId.decode(encoded_id)
            instance = ProfileBankAccounts.objects.filter(user=user, pk=decoded_id).first()
            if instance is None:
                raise ValidationError(f"Bank account with ID {encoded_id} not found for the user.")

            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)

            if data.get('is_primary', False):
                ProfileBankAccounts.objects.filter(user=user, is_primary=True).update(is_primary=False)

            updated_instance = serializer.save()
            updated_instances.append(updated_instance)

        response_serializer = self.get_serializer(updated_instances, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class GovernmentIDViewSet(viewsets.ModelViewSet):
    queryset = GovernmentID.objects.all()
    serializer_class = GovernmentIDSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GovernmentID.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        government_id_instance, created = GovernmentID.objects.update_or_create(
            user=user,
            defaults=serializer.validated_data
        )
        serializer.instance = government_id_instance

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class SendEmailChangeOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        new_email = request.data.get('email')

        if not new_email:
            return Response({'status': 'error', 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=new_email).exists():
            return Response({'status': 'error', 'message': 'This email is already in use by another user'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        otp_service = SendEmailOtpService()
        otp_id = otp_service.send_otp_to_new_email(new_email)
        request.session['email_otp_id'] = otp_id
        request.session['new_email'] = new_email

        return Response({'status': 'success', 'message': 'OTP sent to the new email', 'otp_id': otp_id},
                        status=status.HTTP_200_OK)


class VerifyEmailChangeOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = EmailUpdateOtpSerializer(data=request.data)
        if serializer.is_valid():
            otp_id = serializer.validated_data['otp_id']
            otp = serializer.validated_data['otp']

            try:
                otp_record = OtpRecord.objects.get(id=otp_id, otp=otp)

                if otp_record.is_expired():
                    return Response({'status': 'error', 'message': 'OTP has expired'},
                                    status=status.HTTP_400_BAD_REQUEST)

                user = request.user

                new_email = request.session.get('new_email')

                if not new_email:
                    return Response({'status': 'error', 'message': 'No new email found'},
                                    status=status.HTTP_400_BAD_REQUEST)
                user.email = new_email
                user.save()
                del request.session['email_otp_id']
                del request.session['new_email']
                otp_record.delete()

                return Response({'status': 'success', 'message': 'Email updated successfully'},
                                status=status.HTTP_200_OK)

            except OtpRecord.DoesNotExist:
                return Response({'status': 'error', 'message': 'Invalid OTP or OTP ID'},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendMobileChangeOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        new_mobile_number = request.data.get('mobile_number')

        if not new_mobile_number:
            return Response({'status': 'error', 'message': 'Mobile number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(mobile_number=new_mobile_number).exists():
            return Response({'status': 'error', 'message': 'This mobile number is already in use by another user'}, status=status.HTTP_400_BAD_REQUEST)
        otp_service = SendMobileOtpService()
        success, otp_id = otp_service.send_otp(new_mobile_number)

        if success:
            encoded_otp_id = AlphaId.encode(otp_id)

            return Response({'status': 'success', 'otp_id': encoded_otp_id, 'message': 'OTP sent to the new mobile number'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'message': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyMobileChangeOtpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        encoded_otp_id = request.data.get('otp_id')
        otp = request.data.get('otp')

        if not encoded_otp_id or not otp:
            return Response({'status': 'error', 'message': 'OTP ID and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_id = AlphaId.decode(encoded_otp_id)
            otp_record = OtpRecord.objects.get(id=otp_id, otp=otp, source=OtpRecord.Mobile)
            otp_service = SendMobileOtpService()
            success, message = otp_service.verify_otp(otp_record.mobile_number, otp)

            if success:
                user = request.user
                user.mobile_number = otp_record.mobile_number
                user.save()

                otp_record.delete()

                return Response({'status': 'success', 'message': 'Mobile number updated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'message': message}, status=status.HTTP_400_BAD_REQUEST)

        except OtpRecord.DoesNotExist:
            return Response({'status': 'error', 'message': 'Invalid OTP ID or OTP'}, status=status.HTTP_400_BAD_REQUEST)