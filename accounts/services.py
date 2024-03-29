import random


import requests
from django.conf import settings

from .models import OtpRecord



class SendMobileOtpService:
    def __init__(self, mobile_number):
        self.mobile_number = mobile_number


    def send_otp(self):
        TWOFACTOR_API_KEY = '93a26564-edd8-11ee-8cbb-0200cd936042'
        otp = str(format(random.randint(1000,9999),'04d'))
        response = requests.get('https://api.2factor.in/API/V1/{api_key}/SMS/+91{mobile_number}/AUTOGEN2/BEYONDTAX'.format(
        api_key=TWOFACTOR_API_KEY, mobile_number=self.mobile_number))
        print(response)
        if response.status_code == 200:
            data = response.json()
            otp_session_id = data.get('Details')
            # noinspection PyUnresolvedReferences
            OtpRecord.objects.create(mobile_number=self.mobile_number, otp_authenticator=otp_session_id)
            return True, "OTP sent successfully"
        else:
            return False, "Failed to send OTP"

    def verify_otp(self, otp):
        TWOFACTOR_API_KEY = '93a26564-edd8-11ee-8cbb-0200cd936042'
        # noinspection PyUnresolvedReferences
        otp_record = OtpRecord.objects.get(mobile_number=self.mobile_number)
        response = requests.post('https://api.2factor.in/API/V1/{api_key}/SMS/VERIFY/{session_id}/{otp}'.format(
         api_key=TWOFACTOR_API_KEY, session_id=otp_record.otp_authenticator, otp=otp))

        if response.status_code == 200 and response.json().get('Status') == "Success":
            return True, "OTP verified successfully"
        else:
            return False, "Invalid OTP or OTP expired"



