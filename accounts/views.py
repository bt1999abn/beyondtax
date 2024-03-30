import os

import http.client

from knox.models import AuthToken
from rest_framework.views import APIView
from .services import SendMobileOtpService
from rest_framework.response import Response
from rest_framework import status
from .models import OtpRecord
from django.utils import timezone
from datetime import timedelta

class sendOtpApi(APIView):
    def post(self, request, *args, **kwargs):
        mobile_number = request.data.get('mobile_number')

        if not mobile_number :
            return Response({"error": "Mobile number is required"}, status=status.HTTP_400_BAD_REQUEST)

        service = SendMobileOtpService(mobile_number)
        success, message = service.send_otp()
        if success:
            return Response({"message": message})
        else:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

class verifyOtpApi(APIView):
    def post(self,request,*args , **kwargs):
        mobile_number = request.data.get('mobile_number')
        otp_provided =request.data.get('otp')
        if not mobile_number or not otp_provided:
            return Response({"error": "Mobile number and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp_record = OtpRecord.objects.get(mobile_number=mobile_number)

            if timezone.now() > otp_record.created_at + timedelta(minutes=2):
                return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

            if otp_record.otp == otp_provided:
                if otp_record.otp == otp_provided:

                    user = otp_record.user

                    _, token = AuthToken.objects.create(user)

                    # Return the token in the response
                    return Response({"message": "OTP verified successfully", "token": token})
                else:
                    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except OtpRecord.DoesNotExist:
            return Response({"error": "OTP not found for the provided mobile number."},
                            status=status.HTTP_404_NOT_FOUND)
