import datetime
from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
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


class ProfileInformation(abstract_models.BaseModel):
    MALE, FEMALE, OTHER = 1, 2, 3
    GENDER_CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
        (OTHER, "Other")
    )
    Married, Unmarried, PreferNotToDisclose = 1, 2, 3
    MARRIED_STATUS_CHOICES = (
        (Married, 'married'),
        (Unmarried, 'unmarried'),
        (PreferNotToDisclose, 'prefer not to disclose'),

    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_information')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    fathers_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True)
    gender = models.IntegerField(choices=GENDER_CHOICES,null=True, blank=True)
    maritual_status = models.IntegerField(choices=MARRIED_STATUS_CHOICES,null=True, blank=True)


class ProfileAddress(abstract_models.BaseModel):
    COMMUNICATION, PERMANENT = 1, 2
    ADDRESS_TYPE_CHOICES = (
        (COMMUNICATION, 'Communication Address'),
        (PERMANENT, 'Permanent Address'),
    )
    OWNED, RENTED = 1, 2
    RENT_CHOICES = (
        (OWNED, 'Owned'),
        (RENTED, 'Rented'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_address')
    address_type = models.IntegerField(choices=ADDRESS_TYPE_CHOICES, default=COMMUNICATION)
    rent_status = models.IntegerField(choices=RENT_CHOICES, default=OWNED)
    rental_agreement = models.FileField(upload_to='rental_agreements/', blank=True)
    door_no = models.CharField(max_length=255, blank=True)
    permise_name = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    pincode = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, blank=True)


class ProfileBankAccounts(abstract_models.BaseModel):
    SavingsAccount, CurrentAccount = 1, 2
    TYPE_CHOICES = (
        (SavingsAccount, 'Savings Account'),
        (CurrentAccount, 'Current Account'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_bank_accounts')
    account_no = models.CharField(max_length=255, blank=True)
    ifsc_code = models.CharField(max_length=255, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, blank=True)
    is_primary = models.BooleanField(default=False)


class GovernmentID(abstract_models.BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='government_ids')
    pan_no = models.CharField(max_length=10, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
            message="PAN number must be in format 'ABCDE1234F'"
        )
    ])
    pan_card = models.FileField(upload_to='government_id_proofs/pan/', blank=True, null=True)
    is_pan_verified = models.BooleanField(default=False)

    aadhar_no = models.CharField(max_length=12, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^[0-9]{12}$',
            message="Aadhaar number must be 12 digits"
        )
    ])
    aadhar_card = models.FileField(upload_to='government_id_proofs/aadhar/', blank=True, null=True)
    is_aadhaar_verified = models.BooleanField(default=False)

    driving_license_no = models.CharField(max_length=15, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^[A-Z]{2}[0-9]{13}$',
            message="Driving License number must be in format 'AB1234567890123'"
        )
    ])
    driving_license_card = models.FileField(upload_to='government_id_proofs/driving_license/', blank=True, null=True)
    driving_license_validity = models.DateField(blank=True, null=True)
    is_driving_license_verified = models.BooleanField(default=False)

    voter_id_no = models.CharField(max_length=10, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^[A-Z]{3}[0-9]{7}$',
            message="Voter ID number must be in format 'ABC1234567'"
        )
    ])
    voter_id_card = models.FileField(upload_to='government_id_proofs/voter_id/', blank=True, null=True)
    is_voter_id_verified = models.BooleanField(default=False)

    ration_card_no = models.CharField(max_length=12, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^[A-Z0-9]{10,12}$',
            message="Ration Card number must be between 10 and 12 characters"
        )
    ])
    ration_card = models.FileField(upload_to='government_id_proofs/ration_card/', blank=True, null=True)
    is_ration_card_verified = models.BooleanField(default=False)

    passport_no = models.CharField(max_length=8, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^[A-Z][0-9]{7}$',
            message="Passport number must be in format 'A1234567'"
        )
    ])
    passport = models.FileField(upload_to='government_id_proofs/passport/', blank=True, null=True)
    passport_validity = models.DateField(blank=True, null=True)
    is_passport_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pan_no:
            self.pan_no = self.pan_no.upper()
        if self.aadhar_no:
            self.aadhar_no = self.aadhar_no.upper()
        if self.driving_license_no:
            self.driving_license_no = self.driving_license_no.upper()
        if self.voter_id_no:
            self.voter_id_no = self.voter_id_no.upper()
        if self.ration_card_no:
            self.ration_card_no = self.ration_card_no.upper()
        if self.passport_no:
            self.passport_no = self.passport_no.upper()

        super(GovernmentID, self).save(*args, **kwargs)


class OtpRecord(abstract_models.BaseModel):
    Email, Mobile = 1, 2
    SOURCE_CHOICES =(
        (Email, 'Email'),
        (Mobile, 'Mobile'),
    )
    email = models.EmailField(max_length=255, blank=True)
    mobile_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.IntegerField(choices=SOURCE_CHOICES, null=True, blank=True, default=None)

    def __str__(self):
        return self.mobile_number

    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiration_time


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


class FinancialOwnershipDetails(abstract_models.BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="financial_ownership_details")
    is_partner_in_firm = models.BooleanField(default=False)
    has_unlisted_shares = models.BooleanField(default=False)
    is_director_in_company = models.BooleanField(default=False)
    has_esops = models.BooleanField(default=False)


class UnlistedShareHolding(abstract_models.BaseModel):
    COMPANY_TYPE_CHOICES = [
        ('Private Limited', 'Private Limited'),
        ('Public Limited', 'Public Limited'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="unlisted_share_holdings")

    company_name = models.CharField(max_length=255)
    pan_of_company = models.CharField(max_length=10)
    company_type = models.CharField(choices=COMPANY_TYPE_CHOICES, null=True, blank=True)
    isin_code = models.CharField(max_length=12, blank=True, null=True)
    face_price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_price_per_share = models.DecimalField(max_digits=20, decimal_places=2)
    balance_cost = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.IntegerField()


class DirectorshipDetails(abstract_models.BaseModel):
    COMPANY_TYPE_CHOICES = [
        ('Private Limited', 'Private Limited'),
        ('Public Limited', 'Public Limited'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="directorships")

    company_name = models.CharField(max_length=255)
    pan_of_company = models.CharField(max_length=10)
    company_type = models.CharField(choices=COMPANY_TYPE_CHOICES, null=True, blank=True)
    isin_code = models.CharField(max_length=12, blank=True, null=True)


class EsopDetails(abstract_models.BaseModel):
    COMPANY_TYPE_CHOICES = [
        ('Private Limited', 'Private Limited'),
        ('Public Limited', 'Public Limited'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="esops")

    startup_name = models.CharField(max_length=255)
    pan_of_company = models.CharField(max_length=10)
    company_type = models.CharField(choices=COMPANY_TYPE_CHOICES, null=True, blank=True)
    dpit_reg_no = models.CharField(max_length=50, blank=True, null=True)
    tax_deferred = models.DecimalField(max_digits=10, decimal_places=2)
    balance_tax_payable = models.DecimalField(max_digits=10, decimal_places=2)


class ReturnFilingInformation(abstract_models.BaseModel):
    SECTION_CHOICES = [
        ('Section 139(1)', 'Section 139(1) - On or before the due date'),
        ('Section 139(4)', 'Section 139(4) - Belated return'),
        ('Section 139(5)', 'Section 139(5) - Revised return'),
        ('Section 139(3)', 'Section 139(3) - Loss return'),
        ('Section 92CD', 'Section 92CD - Modified return under APA'),
        ('Section 119(2)(b)', 'Section 119(2)(b) - Return after condonation of delay'),
    ]

    RETURN_TYPE_CHOICES = [
        ('Original', 'Original'),
        ('Revised', 'Revised'),
        ('Modified', 'Modified'),
        ('Belated', 'Belated'),
    ]

    REPRESENTATIVE_ASSESSEE_CHOICES = [
        ('Legal Representative', 'Legal Representative'),
        ('Agent', 'Agent'),
        ('Guardian', 'Guardian'),
        ('Trustee', 'Trustee'),
        ('Any other person representing the assessee', 'Any other person representing the assessee'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="return_filing_info")

    section_filed_under = models.CharField(choices=SECTION_CHOICES, null=True, blank=True)
    return_type = models.CharField(choices=RETURN_TYPE_CHOICES, null=True, blank=True)
    has_representative_access = models.CharField(choices=REPRESENTATIVE_ASSESSEE_CHOICES, null=True, blank=True)