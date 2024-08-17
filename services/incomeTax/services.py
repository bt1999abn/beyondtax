import random
from datetime import timedelta
from django.utils import timezone
from accounts.models import OtpRecord
from accounts.services import EmailService
from shared.libs.hashing import AlphaId


class PanVerificationService:
    def generate_otp(self):
        return random.randint(1000, 9999)

    def send_pan_verification_otp(self, user, pan_number):
        otp = self.generate_otp()
        otp_record = OtpRecord.objects.create(
            email=user.email,
            mobile_number=user.mobile_number,
            otp=str(otp),
            source=OtpRecord.Email,
        )

        context = {
            'user': user.first_name,
            'otp': otp,
            'pan_number': pan_number
        }
        email_service = EmailService()
        email_service.send_email(user.email, 'Your OTP for PAN Verification',
                                 'email_templates/pan_verification_email.html', context)

        return AlphaId.encode(otp_record.id)

    def verify_pan_otp(self, otp_id, otp):
        try:
            otp_record = OtpRecord.objects.get(id=otp_id, otp=otp)
            if timezone.now() < otp_record.created_at + timedelta(minutes=10):
                return True
        except OtpRecord.DoesNotExist:
            return False
        return False