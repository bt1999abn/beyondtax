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


class SalaryIncome(abstract_models.BaseModel):
    Private, CentralGovernment, StateGovernment, PublicSectorUnit = 1, 2, 3, 4
    CATEGORY_TYPE_CHOICES = (
        (Private, 'Private'),
        (CentralGovernment, 'Central Government'),
        (StateGovernment, 'State Government'),
        (PublicSectorUnit, 'Public Sector Unit'),
    )
    Form16, PaySlips = 1, 2
    UPLOAD_FORM_TYPE_CHOICES = (
        (Form16, 'Form16'),
        (PaySlips, 'Pay Slips'),
    )
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='salary_incomes')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE, related_name='salary_incomes')
    employer_name = models.CharField(max_length=255)
    tan = models.CharField(max_length=255)
    employer_category = models.IntegerField(choices=CATEGORY_TYPE_CHOICES)
    tds_deduction = models.DecimalField(max_digits=30, decimal_places=2)
    income_reported = models.DecimalField(max_digits=30, decimal_places=2)
    upload_form_type = models.IntegerField(choices=UPLOAD_FORM_TYPE_CHOICES)
    upload_form_file = models.FileField(upload_to='salary_income_document_files/')
    gross_salary = models.DecimalField(max_digits=30, decimal_places=2)
    basic_salary_component = models.DecimalField(max_digits=30, decimal_places=2)
    hra_component = models.DecimalField(max_digits=30, decimal_places=2)
    annual_rent_paid = models.DecimalField(max_digits=30, decimal_places=2)
    do_you_live_in_these_cities = models.BooleanField()


class RentalIncome(abstract_models.BaseModel):
    LetOut, SelfOccupied = 1, 2
    OCCUPANCY_TYPE_CHOICES = (
        (LetOut, 'Let-out'),
        (SelfOccupied, 'Self-occupied'),
    )
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='rental_incomes')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE, related_name='rental_incomes')
    occupancy_status = models.IntegerField(choices=OCCUPANCY_TYPE_CHOICES)
    tenant_name = models.CharField(max_length=255)
    tenant_aadhar = models.CharField(max_length=255)
    tenant_pan = models.CharField(max_length=255)
    property_door_no = models.CharField(max_length=255)
    property_area = models.CharField(max_length=255)
    property_city = models.CharField(max_length=255)
    property_pincode = models.CharField(max_length=255)
    property_state = models.CharField(max_length=255)
    property_country = models.CharField(max_length=255)
    annual_rent = models.DecimalField(max_digits=30, decimal_places=2)
    property_tax_paid = models.DecimalField(max_digits=30, decimal_places=2)
    standard_deduction = models.DecimalField(max_digits=30, decimal_places=2)
    interest_on_home_loan_dcp = models.DecimalField(max_digits=30, decimal_places=2)
    interest_on_home_loan_pc = models.DecimalField(max_digits=30, decimal_places=2)
    net_rental_income = models.DecimalField(max_digits=30, decimal_places=2)
    ownership_percent = models.IntegerField()


class CapitalGains(abstract_models.BaseModel):
    HouseProperty, ListedSharesOrMutualFunds = 1, 2
    ASSET_TYPE_CHOICES = (
        (HouseProperty, 'House Property'),
        (ListedSharesOrMutualFunds, 'ListedShares/MutualFunds'),
    )
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='capital_gains')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE, related_name='capital_gains')
    asset_type = models.IntegerField(choices=ASSET_TYPE_CHOICES)
    ownership_percent = models.IntegerField()
    purchase_date = models.DateField()
    sale_date = models.DateField()
    held_for_no_of_days = models.IntegerField()
    sale_consideration = models.DecimalField(max_digits=30, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=30, decimal_places=2)
    transfer_expense = models.DecimalField(max_digits=30, decimal_places=2)
    improvement_expense = models.BooleanField()
    description = models.CharField(max_length=255)
    date = models.DateField()
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    gain_or_loss = models.DecimalField(max_digits=30, decimal_places=2)
    property_door_no = models.CharField(max_length=255)
    property_area = models.CharField(max_length=255)
    property_city = models.CharField(max_length=255)
    property_pin = models.CharField(max_length=255)
    property_state = models.CharField(max_length=255)
    property_country = models.CharField(max_length=255)
    stt_paid = models.BooleanField()
    isn_code = models.CharField(max_length=255)
    fund_date = models.DateField()
    fair_value_per_unit = models.DecimalField(max_digits=30, decimal_places=2)
    sale_price_per_unit = models.DecimalField(max_digits=30, decimal_places=2)
    purchase_price_per_unit = models.DecimalField(max_digits=30, decimal_places=2)
    no_of_units = models.IntegerField()


class BuyerDetails(abstract_models.BaseModel):
    capital_gains = models.ForeignKey(CapitalGains, on_delete=models.CASCADE, related_name='buyer_details')
    name = models.CharField(max_length=255)
    pan = models.CharField(max_length=255)
    aadhar = models.CharField(max_length=255)
    percentage_of_ownership = models.IntegerField()


class BusinessIncome(abstract_models.BaseModel):
    BUSINESS_INCOME_TYPE_CHOICES = [
        ('44AD', '44AD'),
        ('44ADA', '44ADA'),
    ]
    Farming, Dairy, Fisheries, TextilesAndGarments, AutomobilesAndAutoComponents, Electronics, Pharmaceuticals, Chemicals, ClothingAndApparel, ITServices = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    INDUSTRY_TYPE_CHOICES = (
        (Farming, 'Farming'),
        (Dairy, 'Dairy'),
        (Fisheries, 'Fisheries'),
        (TextilesAndGarments, 'Textiles And Garments'),
        (AutomobilesAndAutoComponents, 'Automobiles And Auto Components'),
        (Electronics, 'Electronics'),
        (Pharmaceuticals, 'Pharmaceuticals'),
        (Chemicals, 'Chemicals'),
        (ClothingAndApparel, 'Clothing And Apparel'),
        (ITServices, 'IT Services'),
    )
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='business_income')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE, related_name='business_income')
    business_income_type = models.IntegerField(choices=BUSINESS_INCOME_TYPE_CHOICES)
    business_name = models.CharField(max_length=255)
    industry = models.IntegerField(choices=INDUSTRY_TYPE_CHOICES)
    nature_of_business = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    gross_receipt_cheq_neft_rtgs_turnover = models.DecimalField(max_digits=30, decimal_places=2)
    gross_receipt_cheq_neft_rtgs_profit = models.DecimalField(max_digits=30, decimal_places=2)
    gross_receipt_cash_upi_turnover = models.DecimalField(max_digits=30, decimal_places=2)
    gross_receipt_cash_upi_profit = models.DecimalField(max_digits=30, decimal_places=2)
    fixed_asset = models.DecimalField(max_digits=30, decimal_places=2)
    inventory = models.DecimalField(max_digits=30, decimal_places=2)
    receivebles = models.DecimalField(max_digits=30, decimal_places=2)
    loans_and_advances =  models.DecimalField(max_digits=30, decimal_places=2)
    investments = models.DecimalField(max_digits=30, decimal_places=2)
    cash_in_hand = models.DecimalField(max_digits=30, decimal_places=2)
    bank_balance = models.DecimalField(max_digits=30, decimal_places=2)
    other_assets = models.DecimalField(max_digits=30, decimal_places=2)
    capital = models.DecimalField(max_digits=30, decimal_places=2)
    secured_loans = models.DecimalField(max_digits=30, decimal_places=2)
    payables = models.DecimalField(max_digits=30, decimal_places=2)
    unsecured_loans = models.DecimalField(max_digits=30, decimal_places=2)
    advances = models.DecimalField(max_digits=30, decimal_places=2)
    other_liabilities = models.DecimalField(max_digits=30, decimal_places=2)


class AgricultureIncome(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='agriculture_income')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE, related_name='agriculture_income')
    expences = models.DecimalField(max_digits=30, decimal_places=2)
    gross_recipts = models.DecimalField(max_digits=30, decimal_places=2)
    net_income = models.DecimalField(max_digits=30, decimal_places=2)
    previous_unabsorbed_losses = models.DecimalField(max_digits=30, decimal_places=2)


class LandDetails(abstract_models.BaseModel):
    Own, HeldOnLease = 1, 2
    LAND_STATUS_TYPE_CHOICES = (
        (Own, 'Own'),
        (HeldOnLease, 'Held on lease'),
    )
    Irrigated, RainFed = 1, 2
    WATER_SOURCE_TYPE_CHOICES = (
        (Irrigated, 'Irrigated'),
        (RainFed, 'Rain-fed'),
    )
    agriculture_income = models.ForeignKey(AgricultureIncome, on_delete=models.CASCADE, related_name='land_details')
    district = models.CharField(max_length=255)
    measurement = models.DecimalField(max_digits=30, decimal_places=2)
    pincode = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    land_status = models.IntegerField(choices=LAND_STATUS_TYPE_CHOICES)
    water_source = models.IntegerField(choices=WATER_SOURCE_TYPE_CHOICES)


class ExemptIncome(abstract_models.BaseModel):
    PPF, NREAcc, Others = 1, 2, 3
    EXEMPTION_TYPE_CHOICES = (
        (PPF, 'Irrigated'),
        (NREAcc, 'NRE A/C'),
        (Others, 'others'),
    )
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE, related_name='exempt_incomes_agriculture')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE, related_name='exempt_incomes_agriculture')
    exemption_type = models.IntegerField(choices=EXEMPTION_TYPE_CHOICES, default=1)
    particular = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=30, decimal_places=2, null=True)


class InterestIncome(abstract_models.BaseModel):
    SavingsBankAccount, FixedDeposits, Others = 1, 2, 3
    INTEREST_INCOME_TYPE_CHOICES = (
        (SavingsBankAccount, 'Savings Bank A/c'),
        (FixedDeposits, 'Fixed deposits'),
        (Others, 'others'),
    )

    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='exempt_incomes')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='exempt_incomes')
    interest_income_type = models.IntegerField(choices=INTEREST_INCOME_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    interest_amount = models.DecimalField(max_digits=30, decimal_places=2)


class InterestOnItRefunds(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='interest_on_it_refunds')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='interest_on_it_refunds')
    particular = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=30, decimal_places=2)


class DividendIncome(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='dividend_income')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='dividend_income')
    particular = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=30, decimal_places=2)


class IncomeFromBetting(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='income_from_betting')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='income_from_betting')
    particular = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=30, decimal_places=2)


class Deductions(abstract_models.BaseModel):

    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='deductions')
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='deductions')
    life_insurance = models.DecimalField(max_digits=30, decimal_places=2)
    provident_fund = models.DecimalField(max_digits=30, decimal_places=2)
    elss_mutual_fund = models.DecimalField(max_digits=30, decimal_places=2)
    home_loan_repayment = models.DecimalField(max_digits=30, decimal_places=2)
    tution_fees = models.DecimalField(max_digits=30, decimal_places=2)
    stamp_duty_paid = models.DecimalField(max_digits=30, decimal_places=2)
    others = models.DecimalField(max_digits=30, decimal_places=2)
    contribution_by_self = models.DecimalField(max_digits=30, decimal_places=2)
    contribution_by_employeer = models.DecimalField(max_digits=30, decimal_places=2)
    medical_insurance_self = models.DecimalField(max_digits=30, decimal_places=2)
    medical_preventive_health_checkup_self = models.DecimalField(max_digits=30, decimal_places=2)
    medical_expenditure_self = models.DecimalField(max_digits=30, decimal_places=2)
    senior_citizen_self = models.BooleanField()
    medical_insurance_parents = models.DecimalField(max_digits=30, decimal_places=2)
    medical_preventive_health_checkup_parents = models.DecimalField(max_digits=30, decimal_places=2)
    medical_expenditure_parents = models.DecimalField(max_digits=30, decimal_places=2)
    senior_citizen_parents = models.BooleanField()
    education_loan = models.DecimalField(max_digits=30, decimal_places=2)
    electronic_vehicle_loan = models.DecimalField(max_digits=30, decimal_places=2)
    home_loan_taken_year = models.CharField(max_length=255)
    home_loan_amount = models.DecimalField(max_digits=30, decimal_places=2)
    interest_income = models.DecimalField(max_digits=30, decimal_places=2)
    royality_on_books = models.DecimalField(max_digits=30, decimal_places=2)
    income_on_patients = models.DecimalField(max_digits=30, decimal_places=2)
    income_on_bio_degradable = models.DecimalField(max_digits=30, decimal_places=2)
    rent_paid = models.DecimalField(max_digits=30, decimal_places=2)
    contribution_to_agnipath = models.DecimalField(max_digits=30, decimal_places=2)
    donation_to_political_parties = models.DecimalField(max_digits=30, decimal_places=2)
    donation_others = models.DecimalField(max_digits=30, decimal_places=2)


class TdsOrTcsDeduction(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='tds_or_tcs_deduction', null=True)
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='tds_or_tcs_deduction', null=True)
    name_of_deductor = models.CharField(max_length=255)
    tan = models.CharField(max_length=255)
    tds_or_tcs_amount = models.DecimalField(max_digits=30, decimal_places=2)
    gross_receipts = models.DecimalField(max_digits=30, decimal_places=2)


class SelfAssesmentAndAdvanceTaxPaid(abstract_models.BaseModel):
    income_tax = models.ForeignKey(IncomeTaxProfile, on_delete=models.CASCADE,
                                   related_name='self_assesment_and_advance_tax_paid', null=True)
    income_tax_return = models.ForeignKey(IncomeTaxReturn, on_delete=models.CASCADE,
                                          related_name='self_assesment_and_advance_tax_paid', null=True)
    bsr_code = models.CharField(max_length=255)
    challan_no = models.CharField(max_length=255)
    date = models.DateField()
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    upload_challan = models.FileField(upload_to='tax_paid_challan_document_files/')


