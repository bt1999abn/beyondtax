from django.contrib import admin

from services.incomeTax.models import IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxProfile, IncomeTaxReturnYears, \
    IncomeTaxReturn, ResidentialStatusQuestions, ResidentialStatusAnswer, BuyerDetails, LandDetails, SalaryIncome, \
    RentalIncome, CapitalGains, BusinessIncome, AgricultureIncome, ExemptIncome, DividendIncome, \
    InterestIncome, InterestOnItRefunds, TdsOrTcsDeduction, SelfAssesmentAndAdvanceTaxPaid, IncomeFromBetting, Deductions


class IncomeTaxBankDetailsInline(admin.TabularInline):
    model = IncomeTaxBankDetails
    extra = 1


class IncomeTaxAddressInline(admin.TabularInline):
    model = IncomeTaxAddress
    extra = 1


class IncomeTaxProfileAdmin(admin.ModelAdmin):
    inlines = [IncomeTaxAddressInline, IncomeTaxBankDetailsInline,]
    list_display = ('first_name', 'last_name', 'aadhar_no', 'date_of_birth','fathers_name','mobile_number','email')
    search_fields = ('gender', 'residential_status')


class IncomeTaxReturnInline(admin.TabularInline):
    model = IncomeTaxReturn
    extra = 1


class IncomeTaxReturnYearsAdmin(admin.ModelAdmin):
    inlines = [IncomeTaxReturnInline, ]
    list_display = ('name', 'start_date', 'end_date', 'due_date', 'status')
    search_fields = ['status']


class ResidentialStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'slug')
    search_fields = ('question', 'slug')


class ResidentialStatusAnswerAdmin(admin.ModelAdmin):
    list_display = ('id','question', 'answer_text',)
    search_fields = ('question__question', 'answer_text')
    list_filter = ('question', 'income_tax')


class SalaryIncomeAdmin(admin.ModelAdmin):
    list_display = ('employer_name', 'tan', 'employer_category', 'income_tax', 'income_tax_return')
    search_fields = ('employer_name', 'tan')
    list_filter = ('employer_category',)


class RentalIncomeAdmin(admin.ModelAdmin):
    list_display = ('tenant_name', 'tenant_pan', 'occupancy_status', 'annual_rent', 'net_rental_income', 'income_tax', 'income_tax_return')
    search_fields = ('tenant_name', 'tenant_pan')
    list_filter = ('occupancy_status',)


class BuyerDetailsInline(admin.TabularInline):
    model = BuyerDetails
    extra = 1


class CapitalGainsAdmin(admin.ModelAdmin):
    inlines = [BuyerDetailsInline]
    list_display = ('asset_type', 'purchase_date', 'sale_date', 'sale_consideration', 'gain_or_loss', 'income_tax', 'income_tax_return')
    search_fields = ('asset_type',)
    list_filter = ('asset_type',)


class BusinessIncomeAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'industry', 'nature_of_business', 'gross_receipt_cheq_neft_rtgs_turnover', 'income_tax', 'income_tax_return')
    search_fields = ('business_name', 'nature_of_business')
    list_filter = ('industry', 'business_income_type')


class LandDetailsInline(admin.TabularInline):
    model = LandDetails
    extra = 1


class AgricultureIncomeAdmin(admin.ModelAdmin):
    inlines = [LandDetailsInline]
    list_display = ('gross_recipts', 'expences', 'net_income', 'previous_unabsorbed_losses', 'income_tax', 'income_tax_return')
    search_fields = ('gross_recipts', 'net_income')


class ExemptIncomeAdmin(admin.ModelAdmin):
    list_display = ('exemption_type', 'particular', 'amount', 'income_tax', 'income_tax_return')
    search_fields = ('particular', 'description')
    list_filter = ('exemption_type',)


class InterestIncomeAdmin(admin.ModelAdmin):
    list_display = ('interest_income_type', 'description', 'interest_amount', 'income_tax', 'income_tax_return')
    search_fields = ('description',)
    list_filter = ('interest_income_type',)


class InterestOnItRefundsAdmin(admin.ModelAdmin):
    list_display = ('particular', 'description', 'amount', 'income_tax', 'income_tax_return')
    search_fields = ('particular', 'description')


class DividendIncomeAdmin(admin.ModelAdmin):
    list_display = ('particular', 'description', 'amount', 'income_tax', 'income_tax_return')
    search_fields = ('particular', 'description')


class IncomeFromBettingAdmin(admin.ModelAdmin):
    list_display = ('particular', 'description', 'amount', 'income_tax', 'income_tax_return')
    search_fields = ('particular', 'description')


class DeductionsAdmin(admin.ModelAdmin):
    list_display = ('life_insurance', 'provident_fund', 'elss_mutual_fund', 'home_loan_repayment', 'tution_fees', 'medical_insurance_self', 'medical_insurance_parents', 'income_tax', 'income_tax_return')
    search_fields = ('life_insurance', 'provident_fund', 'elss_mutual_fund')
    list_filter = ('home_loan_taken_year', 'senior_citizen_self', 'senior_citizen_parents')


class TdsOrTcsDeductionAdmin(admin.ModelAdmin):
    list_display = ('name_of_deductor', 'tan', 'tds_or_tcs_amount', 'gross_receipts', 'income_tax', 'income_tax_return')
    search_fields = ('name_of_deductor', 'tan')


class SelfAssesmentAndAdvanceTaxPaidAdmin(admin.ModelAdmin):
    list_display = ('bsr_code', 'challan_no', 'date', 'amount', 'income_tax', 'income_tax_return')
    search_fields = ('bsr_code', 'challan_no')


admin.site.register(IncomeTaxProfile, IncomeTaxProfileAdmin)
admin.site.register(IncomeTaxReturnYears, IncomeTaxReturnYearsAdmin)
admin.site.register(ResidentialStatusQuestions, ResidentialStatusAdmin)
admin.site.register(ResidentialStatusAnswer, ResidentialStatusAnswerAdmin)
admin.site.register(SalaryIncome, SalaryIncomeAdmin)
admin.site.register(RentalIncome, RentalIncomeAdmin)
admin.site.register(CapitalGains, CapitalGainsAdmin)
admin.site.register(BusinessIncome, BusinessIncomeAdmin)
admin.site.register(AgricultureIncome, AgricultureIncomeAdmin)
admin.site.register(ExemptIncome, ExemptIncomeAdmin)
admin.site.register(InterestIncome, InterestIncomeAdmin)
admin.site.register(InterestOnItRefunds, InterestOnItRefundsAdmin)
admin.site.register(DividendIncome, DividendIncomeAdmin)
admin.site.register(IncomeFromBetting, IncomeFromBettingAdmin)
admin.site.register(Deductions, DeductionsAdmin)
admin.site.register(TdsOrTcsDeduction, TdsOrTcsDeductionAdmin)
admin.site.register(SelfAssesmentAndAdvanceTaxPaid, SelfAssesmentAndAdvanceTaxPaidAdmin)