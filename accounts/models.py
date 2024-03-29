import datetime

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from accounts import constants as accounts_constants
# from shared import abstract_models
from django.utils import timezone
from datetime import timedelta
from shared import abstract_models
class UserManager(BaseUserManager):
    def filter(self, is_superuser=False, is_staff=False, *args, **kwargs):
        return super(UserManager, self).filter(is_staff=is_staff, is_superuser=is_superuser, *args, **kwargs)

    def create_user(self, email, password, is_active=True, **extra_fields):
        if not email:
            raise ValueError(accounts_constants.EMAIL_NOT_GIVEN_ERROR)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.is_active = is_active
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(accounts_constants.SUPERUSER_NOT_IS_STAFF_ERROR)

        if not extra_fields.get('is_superuser'):
            raise ValueError(accounts_constants.SUPERUSER_NOT_IS_SUPERUSER_ERROR)
        return self.create_user(email, password, **extra_fields)


class User(abstract_models.BaseModel, AbstractUser):
    MALE, FEMALE, OTHER = 1, 2, 3
    GENDER_CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
        (OTHER, "Other")
    )
    username = None
    # TODO: Should we write Transgender in this or not.
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128, blank=True)

    # General Information
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_regex = RegexValidator(regex=r'^([1-9][0-9]{9})$', message=accounts_constants.PHONE_NUMBER_LIMIT_MESSAGE)
    # Validators should be a list
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True)
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_name(self):
        return self.get_full_name()

    def is_admin(self):
        return self.is_staff

    def is_super_admin(self):
        return self.is_superuser

    def save(self, *args, **kwargs):
        if self.date_of_birth and self.date_of_birth > datetime.date.today():
            raise ValidationError(accounts_constants.DOB_IN_FUTURE_ERROR)
        super(User, self).save(*args, **kwargs)
# class User(AbstractUser):
#     CHOICES=()
#     mobilenumber_regex =RegexValidator(regex=r'^\+?1?\d{9,10}$', message ="mobile number must be entered in the format +919999999999.up to")
#     otp_regex=RegexValidator(regex=r"^\d{4}$", message="please enter valid otp format ")
#     mobilenumber=models.charField('mobile',validators=[mobilenumber_regex],max_length=10,unique=True,null=True)
#     otp=models.charField('otp', validators=[otp_regex], max_length=4,unique=True,null=True)
#     REQUIRED_FIELD=[mobilenumber]
#     Required_field=[otp]


        # def __str__(self):
            # return self.mobile_number


class OtpRecord(models.Model):
    mobile_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=4)
    otp_authenticator = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now() + timedelta(minutes=2))
    def __str__(self):
        return self.mobile_number