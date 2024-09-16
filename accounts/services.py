import threading
import uuid

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
import random
from typing import Dict, Any
import requests
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from urllib.parse import urlencode
from django.utils.html import strip_tags
import beyondTax
from beyondTax import settings
from .models import OtpRecord, User


class SendMobileOtpService:
    OTP_TEMPLATE_NAME = "BEYONDTAX"
    TWO_FACTOR_SEND_OTP_URL = "https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}/{otp_template}"
    TWOFACTOR_API_KEY = 'e64cf901-f976-11ee-8cbb-0200cd936042'

    def generate_otp(self):
        return str(format(random.randint(1000, 9999), '04d'))

    def send_otp(self, phone_number):
        otp = self.generate_otp()
        url = self.TWO_FACTOR_SEND_OTP_URL.format(
            api_key=self.TWOFACTOR_API_KEY, phone_number=phone_number, otp=otp, otp_template=self.OTP_TEMPLATE_NAME
        )
        response = requests.post(url)
        if response.status_code == 200:
            # Create OtpRecord in the database
            otp_record = OtpRecord.objects.create(
                mobile_number=phone_number,
                otp=otp,
                source=OtpRecord.Mobile
            )
            return True, otp_record.id
        else:
            return False, "Failed to send OTP"

    def verify_otp(self, phone_number, otp):
        try:
            otp_record = OtpRecord.objects.get(mobile_number=phone_number, otp=otp, source=OtpRecord.Mobile)
            if timezone.now() < otp_record.created_at + timedelta(minutes=10):
                return True, "OTP verified successfully"
            else:
                return False, "OTP has expired"
        except OtpRecord.DoesNotExist:
            return False, "Invalid OTP or mobile number"


GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
LOGIN_URL = f'{settings.FRONTEND_HOST}/internal/login'


def google_get_access_token(code: str, redirect_uri: str) -> str:
    data = {
        'code': code,
        'client_id': beyondTax.settings.GOOGLE_OAUTH2_CLIENT_ID,
        'client_secret': beyondTax.settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
    if not response.ok:
        raise ValidationError('Could not get access token from Google.')

    access_token = response.json()['access_token']

    return access_token


def google_get_user_info(access_token: str) -> Dict[str, Any]:
    response = requests.get(
        GOOGLE_USER_INFO_URL,
        params={'access_token': access_token}
    )

    if not response.ok:
        raise ValidationError('Could not get user info from Google.')

    return response.json()


def get_user_data(validated_data):
    domain = settings.BACKEND_BASE_URL
    redirect_uri = f'{domain}/auth/api/login/google/'

    code = validated_data.get('code')
    error = validated_data.get('error')

    if error or not code:
        params = urlencode({'error': error})
        return redirect(f'{LOGIN_URL}?{params}')

    access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
    user_data = google_get_user_info(access_token=access_token)

    User.objects.get_or_create(
        email=user_data['email'],
        first_name=user_data.get('given_name'),
        last_name=user_data.get('family_name'),
        is_active=True
    )

    profile_data = {
        'email': user_data['email'],
        'first_name': user_data.get('given_name'),
        'last_name': user_data.get('family_name'),
        'is_active': 'True',
    }
    return profile_data


class SendEmailOtpService:

    def generate_otp(self):
        return random.randint(1000, 9999)

    def send_otp_email(self, user, otp, template='otp_email'):
        subject = 'Your OTP for Verification'
        first_name = user.first_name
        html_message = render_to_string(f'email_templates/{template}.html', {'user': first_name, 'otp': otp})
        plain_message = strip_tags(html_message)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, plain_message, email_from, recipient_list, html_message=html_message)

    def send_otp_to_new_email(self, new_email, template='email_id_update'):
        otp = self.generate_otp()
        otp_record = OtpRecord.objects.create(
            email=new_email,
            otp=str(otp),
            source=OtpRecord.Email
        )
        email_thread = threading.Thread(target=self.send_otp_email, args=(new_email, otp, template, None))
        email_thread.start()

        return otp_record.id

    def send_otp(self, user, template='otp_email'):
        otp = self.generate_otp()
        otp_record = OtpRecord.objects.create(
            email=user.email,
            mobile_number=user.mobile_number,
            otp=str(otp),
            source=OtpRecord.Email,
        )
        email_thread = threading.Thread(target=self.send_otp_email, args=(user, otp, template))
        email_thread.start()
        return otp_record.id

    def verify_otp(self, otp_id, otp):
        try:
            otp_record = OtpRecord.objects.get(id=otp_id, otp=otp)
            if timezone.now() < otp_record.created_at + timedelta(minutes=10):
                return True
        except OtpRecord.DoesNotExist:
            return False
        return False


class EmailService:

    def send_email(self, recipient_email, subject,  template_path, context):
        html_message = render_to_string(template_path, context)
        plain_message = strip_tags(html_message)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [recipient_email]

        email_thread = threading.Thread(target=send_mail, args=(subject, plain_message, email_from, recipient_list,), kwargs={'html_message': html_message})
        email_thread.start()