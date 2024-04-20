import datetime
from decimal import Decimal
from ckeditor.fields import RichTextField
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
         ('Andhra Pradesh', 'Andhra Pradesh'),
         ('Arunachal Pradesh', 'Arunachal Pradesh'),
         ('Assam', 'Assam'),
         ('Bihar', 'Bihar'),
         ('Chhattisgarh', 'Chhattisgarh'),
         ('Goa', 'Goa'),
         ('Gujarat', 'Gujarat'),
         ('Haryana', 'Haryana'),
         ('Himachal Pradesh', 'Himachal Pradesh'),
         ('Jammu and Kashmir', 'Jammu and Kashmir'),
         ('Jharkhand', 'Jharkhand'),
         ('Karnataka', 'Karnataka'),
         ('Kerala', 'Kerala'),
         ('Madhya Pradesh', 'Madhya Pradesh'),
         ('Maharashtra', 'Maharashtra'),
         ('Manipur', 'Manipur'),
         ('Meghalaya', 'Meghalaya'),
         ('Mizoram', 'Mizoram'),
         ('Nagaland', 'Nagaland'),
         ('Odisha', 'Odisha'),
         ('Punjab', 'Punjab'),
         ('Rajasthan', 'Rajasthan'),
         ('Sikkim', 'Sikkim'),
         ('Tamil Nadu', 'Tamil Nadu'),
         ('Telangana', 'Telangana'),
         ('Tripura', 'Tripura'),
         ('Uttar Pradesh', 'Uttar Pradesh'),
         ('Uttarakhand', 'Uttarakhand'),
         ('West Bengal', 'West Bengal'),
         ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
         ('Chandigarh', 'Chandigarh'),
         ('Dadra and Nagar Haveli', 'Dadra and Nagar Haveli'),
         ('Daman and Diu', 'Daman and Diu'),
         ('Delhi', 'Delhi'),
         ('Lakshadweep', 'Lakshadweep'),
         ('Puducherry', 'Puducherry'),
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
    is_active = models.BooleanField(default=False)
    email = models.CharField(max_length=255, blank=True)
    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'state', 'password']

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        first_name = " ".join(word.capitalize() for word in self.first_name.split()) if self.first_name else ''
        last_name = " ".join(word.capitalize() for word in self.last_name.split()) if self.last_name else ''
        return f'{first_name} {last_name}'.strip()

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
    required_documents = models.JSONField(default=dict)


class WorkOrder(abstract_models.BaseModel):
    Inprocess, Available, Canceled = 1, 2, 3
    STATUS_CHOICES = (
        (Inprocess, "Inprocess"),
        (Available, "Available"),
        (Canceled, "Canceled")
    )
    service_name = models.CharField(max_length=255, blank=False)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=Decimal('0.00'),  blank=False)
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=False, default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='work_orders')
    service = models.ForeignKey(ServicePages, related_name='work_order_files', null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.service:
            self.service_name = self.service.service_title
        super(WorkOrder, self).save(*args, **kwargs)


class WorkOrderFiles(abstract_models.BaseModel):
    work_order = models.ForeignKey(WorkOrder, related_name='work_order', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, blank=False, default='file name')
    files = models.FileField(upload_to='work_order_files/')


class BlogPost(abstract_models.BaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(default='Default description')
    content = RichTextField()
    category = models.CharField(max_length=100, blank=True, null=True)