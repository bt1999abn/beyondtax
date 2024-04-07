import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from accounts import constants as accounts_constants
from shared import abstract_models


class UserManager(BaseUserManager):
    def create_user(self, mobile_number, password, is_active=True, **extra_fields):
        if not mobile_number:
            raise ValueError("Mobile number is required")
        user = self.model(mobile_number=mobile_number, **extra_fields)
        user.is_active = is_active
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, mobile_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(accounts_constants.SUPERUSER_NOT_IS_STAFF_ERROR)

        if not extra_fields.get('is_superuser'):
            raise ValueError(accounts_constants.SUPERUSER_NOT_IS_SUPERUSER_ERROR)
        return self.create_user(mobile_number, password, **extra_fields)


class User(abstract_models.BaseModel, AbstractUser):

    MALE, FEMALE, OTHER = 1, 2, 3
    GENDER_CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
        (OTHER, "Other")
    )
    STATES_CHOICES = [
         ('AP', 'Andhra Pradesh'),
         ('AR', 'Arunachal Pradesh'),
         ('AS', 'Assam'),
         ('BR', 'Bihar'),
         ('CT', 'Chhattisgarh'),
         ('GA', 'Goa'),
         ('GJ', 'Gujarat'),
         ('HR', 'Haryana'),
         ('HP', 'Himachal Pradesh'),
         ('JK', 'Jammu and Kashmir'),
         ('JH', 'Jharkhand'),
         ('KA', 'Karnataka'),
         ('KL', 'Kerala'),
         ('MP', 'Madhya Pradesh'),
         ('MH', 'Maharashtra'),
         ('MN', 'Manipur'),
         ('ML', 'Meghalaya'),
         ('MZ', 'Mizoram'),
         ('NL', 'Nagaland'),
         ('OR', 'Odisha'),
         ('PB', 'Punjab'),
         ('RJ', 'Rajasthan'),
         ('SK', 'Sikkim'),
         ('TN', 'Tamil Nadu'),
         ('TG', 'Telangana'),
         ('TR', 'Tripura'),
         ('UP', 'Uttar Pradesh'),
         ('UT', 'Uttarakhand'),
         ('WB', 'West Bengal'),
         ('AN', 'Andaman and Nicobar Islands'),
         ('CH', 'Chandigarh'),
         ('DN', 'Dadra and Nagar Haveli'),
         ('DD', 'Daman and Diu'),
         ('DL', 'Delhi'),
         ('LD', 'Lakshadweep'),
         ('PY', 'Puducherry'),
     ]

    username = None
    # TODO: Should we write Transgender in this or not.
    password = models.CharField(max_length=128, blank=True)

    # General Information

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    mobile_regex = RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message=accounts_constants.PHONE_NUMBER_LIMIT_MESSAGE
    )
    # Validators should be a list
    mobile_number = models.CharField(validators=[mobile_regex], unique=True, max_length=10, blank=True)
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, null=True, blank=True)
    state = models.CharField(choices=STATES_CHOICES, null=True, blank=True)

    email = models.CharField( max_length=255, blank=True )
    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'state']

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


class OtpRecord(abstract_models.BaseModel):
    mobile_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=4)
    otp_session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mobile_number


class ServicePages(abstract_models.BaseModel):
    service_title = models.CharField(max_length=255 , default='Default Title')
    service_description = models.TextField(default='Default description')
    certificate_price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))

    registration_title = models.CharField(max_length=255 , default='Default Title')
    what_is = models.JSONField(default=dict)

    step_by_step_title = models.CharField(max_length=255 , default='Default Title')
    step_by_step_description = models.JSONField(default=dict)

    faq_title= models.CharField(max_length=255 , default='Default Title')
    faq_description = models.TextField(default='Default description')
    faq = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)