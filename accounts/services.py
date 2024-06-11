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
    def __init__(self):
        self.OTP_TEMPLATE_NAME = "BEYONDTAX"
        self.TWO_FACTOR_SEND_OTP_URL = "https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}/{otp_template}"
        self.TWO_FACTOR_VERIFY_OTP_URL = "https://api.2factor.in/API/V1/{api_key}/SMS/VERIFY/{session_id}/{otp}"
        self.TWOFACTOR_API_KEY = 'e64cf901-f976-11ee-8cbb-0200cd936042'

    def send_otp(self, phone_number):
        print(phone_number)
        otp = str(format(random.randint(1000, 9999), '04d'))
        url = self.TWO_FACTOR_SEND_OTP_URL.format(
            api_key=self.TWOFACTOR_API_KEY, phone_number=phone_number, otp=otp, otp_template=self.OTP_TEMPLATE_NAME
        )
        response = requests.post(url)
        if response.status_code == 200:
            data = response.json()
            otp_session_id = data.get('Details')
            # noinspection PyUnresolvedReferences
            OtpRecord.objects.create(
                mobile_number=phone_number, otp_session_id=otp_session_id,
                otp=otp
            )
            return True, otp_session_id
        else:
            return False, "Failed to send OTP"

    def verify_otp(self, otp):
        # noinspection PyUnresolvedReferences
        otp_record = OtpRecord.objects.get(mobile_number=self.mobile_number)
        url = self.TWO_FACTOR_VERIFY_OTP_URL.format(
            api_key=self.TWOFACTOR_API_KEY, session_id=otp_record.otp_session_id, otp=otp
        )
        response = requests.get(url)

        if response.status_code == 200 and response.json().get('Status') == "Success":
            return True, "OTP verified successfully"
        else:
            return False, "Invalid OTP or OTP expired"


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

    def send_otp_email(self, user, otp):
        subject = 'Your OTP for Password Reset'
        first_name = user.first_name
        html_message = render_to_string('email_templates/otp_email.html', {'user': first_name, 'otp': otp})
        plain_message = strip_tags(html_message)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, plain_message, email_from, recipient_list, html_message=html_message)

    def send_otp(self, user):
        otp = self.generate_otp()
        OtpRecord.objects.create(
            email=user.email,
            mobile_number=user.mobile_number,
            otp=str(otp),
            otp_session_id=str(uuid.uuid4()),
            source=OtpRecord.Email,
        )
        email_thread = threading.Thread(target=self.send_otp_email, args=(user, otp))
        email_thread.start()

    def verify_otp(self, email, otp):
        try:
            otp_record = OtpRecord.objects.get(email=email, otp=otp)
            if timezone.now() < otp_record.created_at + timedelta(minutes=10):
                otp_record.delete()
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