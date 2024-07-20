from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

from beyondTax import settings
from shared import abstract_models
from accounts import constants as accounts_constants


class IncomeTaxProfile(abstract_models.BaseModel):
    MALE, FEMALE, OTHER = 1, 2, 3
    GENDER_CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
        (OTHER, "Other")
    )
    Married, Unmarried, PreferNotToDisclose = 1, 2, 3
    MARRIED_STATUS_CHOICES =(
        (Married, 'married'),
        (Unmarried, 'unmarried'),
        (PreferNotToDisclose, 'prefer not to disclose'),

    )
    IndianResident, NonResidentIndian, IndianResidentButNotOrdinary, IndianResidentButOrdinary  = 1, 2, 3, 4
    RESIDENTIAL_STATUS_CHOICES =(
        (IndianResident, 'Indian Resident'),
        (NonResidentIndian, 'Non-Resident Indian'),
        (IndianResidentButNotOrdinary, 'IndianResident(NotOrdinary)'),
        (IndianResidentButOrdinary, 'IndianResident(Ordinary)'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='income_tax_profile')
    first_name = models.CharField(max_length=255, blank=True)
    middle_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    fathers_name = models.CharField(max_length=255, blank=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, blank=True)
    marital_status = models.IntegerField(choices=MARRIED_STATUS_CHOICES, blank=True)
    aadhar_no = models.CharField(max_length=12, blank=True)
    aadhar_enrollment_no = models.CharField(max_length=28, blank=True)
    pan_no = models.CharField(max_length=10, blank=True)
    mobile_regex = RegexValidator(
        regex=r'^([1-9][0-9]{9})$', message=accounts_constants.PHONE_NUMBER_LIMIT_MESSAGE
    )
    mobile_number = models.CharField(validators=[mobile_regex], max_length=10, blank=True)
    email = models.CharField(max_length=255, blank=True)
    residential_status = models.IntegerField(choices=RESIDENTIAL_STATUS_CHOICES, blank=True)
    is_pan_verified = models.BooleanField(default=False, blank=True)
    is_data_imported = models.BooleanField(default=False, blank=True)
    REQUIRED_FIELDS = 'pan_no'


class IncomeTaxBankDetails(abstract_models.BaseModel):
    SavingsAccount, CurrentAccount = 1, 2
    TYPE_CHOICES = (
        (SavingsAccount, 'Savings Account'),
        (CurrentAccount, 'Current Account'),
    )
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,  related_name='income_tax_bankdetails')
    account_no = models.CharField(max_length=255, blank=True)
    ifsc_code = models.CharField(max_length=255, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, blank=True)


class IncomeTaxAddress(abstract_models.BaseModel):
    income_tax = models.OneToOneField(IncomeTaxProfile, on_delete=models.CASCADE,  related_name='address')
    door_no = models.CharField(max_length=255, blank=True)
    permise_name = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    pincode = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, blank=True)


class IncomeTaxReturnYears(abstract_models.BaseModel):
    Open, Closed = 1, 2
    STATUS_CHOICES = (
        (Open, 'open'),
        (Closed, 'closed'),
    )
    name = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    due_date = models.DateField()
    status = models.IntegerField(choices=STATUS_CHOICES, blank=True)


class IncomeTaxReturn(abstract_models.BaseModel):
    NotFiled, PartiallyFiled, Filed = 1, 2, 3
    STATUS_CHOICES =(
        (NotFiled, 'Not Filed'),
        (PartiallyFiled, 'Partially Filed'),
        (Filed, 'Filed'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='income_tax_returns')
    income_tax_return_year = models.ForeignKey(IncomeTaxReturnYears, on_delete=models.CASCADE, related_name='income_tax_return_year')
    status = models.IntegerField(choices=STATUS_CHOICES, blank=True, default=1)

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Unknown')


class ResidentialStatusQuestions(abstract_models.BaseModel):
    ToggledButtons, DropDown, RadioButtons, AutoComplete, MultiSelect = 1, 2, 3, 4, 5
    OPTIONS_TYPE_CHOICES = (
        (ToggledButtons, 'Toggled Buttons'),
        (DropDown, 'Drop Down'),
        (RadioButtons, 'Radio Buttons'),
        (AutoComplete, 'Auto Complete'),
        (MultiSelect, 'Multi Select'),
    )
    question = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    options = models.JSONField(default=list)
    options_type = models.IntegerField(choices=OPTIONS_TYPE_CHOICES, default=1)
    sequence = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.question)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question


class ResidentialStatusAnswer(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='status_answers')
    question = models.ForeignKey(ResidentialStatusQuestions, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255)


