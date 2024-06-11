import datetime
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from accounts import constants as accounts_constants
from shared import abstract_models
from django.utils.translation import gettext_lazy as _


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
    Individual, Proprietorship, HUF, Firm, LLP, PrivateLimitedCompany, PublicLimitedCompany, Trust = 1, 2, 3, 4, 5, 6, 7, 8
    CLIENT_TYPE_CHOICES = (
        (Individual, "Individual"),
        (Proprietorship, "Proprietorship"),
        (HUF, "HUF"),
        (Firm, "Firm"),
        (LLP, "LLP"),
        (PrivateLimitedCompany, "Private Limited Company"),
        (PublicLimitedCompany, "Public Limited Company"),
        (Trust, "Trust"),
    )
    INDUSTRY_TYPE_CHOICES = [
        ("Consultancy", "Consultancy"),
        ("Technology", "Technology"),
        ("Construction", "Construction"),
        ("Clothing", "Clothing"),
        ("Agriculture", "Agriculture"),
        ("Salaried", "Salaried"),
        ("Real Estate", "Real Estate"),
        ("Food & beverage", "Food & beverage"),
        ("Consulting", "Consulting"),
        ("Rental", "Rental"),
        ("Sports", "Sports"),
        ("Decors", "Decors"),
        ("Retail", "Retail"),
        ("Healthcare", "Healthcare"),
    ]
    NATURE_OF_BUSINESS_CHOICES = [
        ('Service', 'Service'),
        ('Manufacturing', 'Manufacturing'),
        ('Retailer', 'Retailer'),
        ('Wholesaler', 'Wholesaler'),
    ]
    NUMBER_OF_EMPLOYEES_CHOICES = [
        ('Upto 5 Employees', 'Upto 5 Employees'),
        ('Upto 25 Employees', 'Upto 25 Employees'),
        ('Above 25 Employees', 'Above 25 Employees'),
    ]

    username = None
    # TODO: Should we write Transgender in this or not.
    password = models.CharField(max_length=128, blank=True)

    # General Information

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True,null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    mobile_regex = RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message=accounts_constants.PHONE_NUMBER_LIMIT_MESSAGE
    )
    # Validators should be a list
    mobile_number = models.CharField(validators=[mobile_regex], max_length=10, blank=True)
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, null=True, blank=True)
    state = models.CharField(choices=STATES_CHOICES, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    email = models.EmailField(_('email address'), blank=True)
    client_type = models.IntegerField(choices=CLIENT_TYPE_CHOICES, null=True, blank=True, default=None)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    industry_type = models.CharField(choices=INDUSTRY_TYPE_CHOICES, null=True, blank=True, default="PLEASE SELECT INDUSTRY TYPE")
    nature_of_business = models.CharField(choices=NATURE_OF_BUSINESS_CHOICES, null=True, blank=True, default="PLEASE SELECT Nature of business")
    contact_person = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    contact_person_phone_number = models.CharField(max_length=10, blank=True)
    contact_email = models.CharField(max_length=255, blank=True)
    date_of_formation = models.DateField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=30, decimal_places=2, default=Decimal('0.00'))
    business_name = models.CharField(max_length=255, blank=True)
    number_of_employees = models.CharField(choices=NUMBER_OF_EMPLOYEES_CHOICES, max_length=50, null=True, blank=True)
    business_mobile_number = models.CharField(max_length=10, blank=True)
    business_email = models.CharField(max_length=255, blank=True)
    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'state', 'password','email']

    objects = UserManager()

    def __str__(self):
        return self.mobile_number

    def get_full_name(self):
        first_name = " ".join(word.capitalize() for word in self.first_name.split()) if self.first_name else ''
        last_name = " ".join(word.capitalize() for word in self.last_name.split()) if self.last_name else ''
        return f'{first_name} {last_name}'.strip()

    def get_profile_title(self):
        if self.client_type == self.Individual:
            if self.first_name and self.last_name:
                return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
            return None
        else:
            return self.business_name

    def full_name(self):
        return self.get_full_name()

    def profile_title(self):
        return self.get_profile_title()

    def is_admin(self):
        return self.is_staff

    def is_super_admin(self):
        return self.is_superuser

    def save(self, *args, **kwargs):
        if self.date_of_birth and self.date_of_birth > datetime.date.today():
            raise ValidationError(accounts_constants.DOB_IN_FUTURE_ERROR)
        super(User, self).save(*args, **kwargs)


class OtpRecord(abstract_models.BaseModel):
    Email, Mobile = 1, 2
    SOURCE_CHOICES =(
        (Email, 'Email'),
        (Mobile, 'Mobile'),
    )
    email = models.EmailField(max_length=255, blank=True)
    mobile_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=4)
    otp_session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.IntegerField(choices=SOURCE_CHOICES, null=True, blank=True, default=None)

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
    certificate_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

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


class UpcomingDueDates(abstract_models.BaseModel):
    BusinessEssentials, TaxRelated, EntityFormation, IncomeTax, GST, Accounting, CompanyCompliance, TDS = 1, 2, 3, 4, 5, 6, 7, 8
    SERVICE_TYPE_CHOICES = (
        (BusinessEssentials, "Business Essentials"),
        (TaxRelated, "Tax Related"),
        (EntityFormation, "Entity Formation"),
        (IncomeTax, "Income Tax"),
        (GST, "GST"),
        (Accounting, "Accounting"),
        (CompanyCompliance, "Company Compliance"),
        (TDS, "TDS"),
    )
    date = models.DateField( null=True, blank=True)
    compliance_activity = models.CharField(max_length=255, null=True, blank=True)
    service_type = models.IntegerField(choices=SERVICE_TYPE_CHOICES, null=True, blank=True)
    penalty_fine_interest = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"UpcomingDueDates ID: {self.id}"


class BusinessContactPersonDetails(abstract_models.BaseModel):
    TIMING_CHOICES = [
        ('9AM - 12PM', '9AM - 12PM'),
        ('12PM - 5PM', '12PM - 5PM'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_persons')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    preferred_timing = models.CharField(choices=TIMING_CHOICES, null=True, blank=True)
    email = models.EmailField()
    mobile_regex = RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message=accounts_constants.PHONE_NUMBER_LIMIT_MESSAGE
    )
    mobile_number = models.CharField(validators=[mobile_regex], max_length=10)



