import datetime
import random
import requests

from .models import OtpRecord


class SendMobileOtpService:
    def __init__(self):
        self.OTP_TEMPLATE_NAME = "BEYONDTAX"
        self.TWO_FACTOR_SEND_OTP_URL = "https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}/{otp_template}"
        self.TWO_FACTOR_VERIFY_OTP_URL = "https://api.2factor.in/API/V1/{api_key}/SMS/VERIFY/{session_id}/{otp}"
        self.TWOFACTOR_API_KEY = 'f149496a-f377-11ee-8cbb-0200cd936042'

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


