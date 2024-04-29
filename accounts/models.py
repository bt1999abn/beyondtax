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
    Individual, Proprietorship, Firm, LLP, Company, Trust = 1, 2, 3, 4, 5, 6
    CLIENT_TYPE_CHOICES = (
        (Individual, "Individual"),
        (Proprietorship, "Proprietorship"),
        (Firm, "Firm"),
        (LLP, "LLP"),
        (Company, "Company"),
        (Trust, "Trust"),
    )
    INDUSTRY_TYPE_CHOICES = [
        ("Technology and IT", "Technology and IT"),
        ("Healthcare and pharmaceuticals", "Healthcare and pharmaceuticals"),
        ("Finance and banking", "Finance and banking"),
        ("Manufacturing and production", "Manufacturing and production"),
        ("Retail and e-commerce", "Retail and e-commerce"),
        ("Energy and utilities", "Energy and utilities"),
        ("Transportation and logistics", "Transportation and logistics"),
        ("Media and entertainment", "Media and entertainment"),
        ("Food and beverage", "Food and beverage"),
        ("Hospitality and tourism", "Hospitality and tourism"),
    ]
    NATURE_OF_BUSINESS_CHOICES = [
        ('Service', 'Service'),
        ('Manufacturing', 'Manufacturing'),
        ('Trading', 'Trading'),
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
    client_type = models.IntegerField(choices=CLIENT_TYPE_CHOICES, null=True, blank=True, default=None)
    industry_type = models.CharField(choices=INDUSTRY_TYPE_CHOICES, null=True, blank=True, default="PLEASE SELECT INDUSTRY TYPE")
    nature_of_business = models.CharField(choices=NATURE_OF_BUSINESS_CHOICES, null=True, blank=True, default="PLEASE SELECT Nature of business")
    contact_person = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    contact_person_phone_number = models.CharField(max_length=10, blank=True)
    contact_email = models.CharField(max_length=255, blank=True)
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
    BusinessEssentials, TaxRelated, EntityFormation, IncomeTax, GST, Accounting, CompanyCompliance, TDS = 1, 2, 3, 4, 5, 6, 7, 8
    CATEGORY_CHOICES = (
        (BusinessEssentials, "Business Essentials"),
        (TaxRelated, "Tax Related"),
        (EntityFormation, "Entity Formation"),
        (IncomeTax, "Income Tax"),
        (GST, "GST"),
        (Accounting, "Accounting"),
        (CompanyCompliance, "Company Compliance"),
        (TDS, "TDS"),
    )
    Individual, Proprietorship, Firm, LLP, Company, Trust = 1, 2, 3, 4, 5, 6
    CLIENT_TYPE_CHOICES = (
        (Individual, "Individual"),
        (Proprietorship, "Proprietorship"),
        (Firm, "Firm"),
        (LLP, "LLP"),
        (Company, "Company"),
        (Trust, "Trust"),
    )
    Daily, Weekly, Monthly, Quarterly, HalfYearly, Yearly = 1, 2, 3, 4, 5, 6
    FREQUENCY_CHOICES =(
        (Daily, "Daily"),
        (Weekly, "Weekly"),
        (Monthly, "Monthly"),
        (Quarterly, "Quarterly"),
        (HalfYearly, "Half-Yearly"),
        (Yearly, "Yearly"),
    )
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
    required_documents = models.CharField(max_length=255)
    category = models.IntegerField(choices=CATEGORY_CHOICES, null=True, blank=True, default=None)
    client_type = models.IntegerField(choices=CLIENT_TYPE_CHOICES, null=True, blank=True, default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="listing_price")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="effective_price")
    due_date = models.DateField(null=True, blank=True)
    government_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    due_duration = models.PositiveIntegerField(default=10)
    frequency = models.IntegerField(choices=FREQUENCY_CHOICES, null=True, blank=True, default=None)

    def get_required_documents_list(self):
        return [doc.strip() for doc in self.required_documents.split(',') if doc.strip()]


class WorkOrder(abstract_models.BaseModel):
    Requested, Upload, Inprocess, Pay, Download= 1, 2, 3, 4, 5
    STATUS_CHOICES = (
        (Requested, "Requested"),
        (Upload, "Upload"),
        (Inprocess, "Inprocess"),
        (Pay, "Pay"),
        (Download, "Download"),

    )
    service_name = models.CharField(max_length=255, blank=False)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=Decimal('0.00'),  blank=False)
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=False, default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='work_orders')
    service = models.ForeignKey(ServicePages, related_name='work_order_files', null=True, on_delete=models.CASCADE)
    wo_dept = models.CharField(max_length=255, blank=True)
    requested_by = models.CharField(max_length=255, blank=True)
    client_id = models.IntegerField(blank=True, null=True)
    client_type = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    frequency = models.CharField(max_length=255, blank=True)
    schedule_date = models.DateField(blank=True, null=True)
    schedule_time = models.TimeField(blank=True, null=True)
    started_on = models.DateTimeField(blank=True, null=True)
    ended_on = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):

        if self.service:
            self.wo_dept = self.service.category
            self.service_name = self.service.service_title
            self.frequency = self.service.frequency
        if self.user:
            self.client_id = self.user.id
            self.requested_by = self.user.first_name
            self.client_type = self.user.client_type
        super(WorkOrder, self).save(*args, **kwargs)


class WorkOrderDocument(abstract_models.BaseModel):
    work_order = models.ForeignKey(WorkOrder, related_name='work_order', on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255, blank=False, default='file name')
    document_file = models.FileField(upload_to='work_order_document_files/')


class WorkOrderDownloadDocument(abstract_models.BaseModel):
    work_order = models.ForeignKey('WorkOrder', on_delete=models.CASCADE)
    download_document = models.FileField(upload_to='work_order_download_documents/')
    description = models.CharField(max_length=255, blank=True)



