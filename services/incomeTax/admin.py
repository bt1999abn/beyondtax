from django.contrib import admin

from services.incomeTax.models import IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxProfile, IncomeTaxReturnYears, \
    IncomeTaxReturn


class IncomeTaxBankDetailsInline(admin.TabularInline):
    model = IncomeTaxBankDetails
    extra = 1


class IncomeTaxAddressInline(admin.TabularInline):
    model = IncomeTaxAddress
    extra = 1


class IncomeTaxProfileAdmin(admin.ModelAdmin):
    inlines = [IncomeTaxAddressInline, IncomeTaxBankDetailsInline,]
    list_display = ('first_name', 'last_name', 'aadhar_no', 'date_of_birth','fathers_name','mobile_number','email')
    search_fields = ['gender', 'residential_status']


class IncomeTaxReturnInline(admin.TabularInline):
    model = IncomeTaxReturn
    extra = 1


class IncomeTaxReturnYearsAdmin(admin.ModelAdmin):
    inlines = [IncomeTaxReturnInline, ]
    list_display = ('start_date', 'end_date', 'due_date', 'status')
    search_fields = ['status']


admin.site.register(IncomeTaxProfile, IncomeTaxProfileAdmin)
admin.site.register(IncomeTaxReturnYears, IncomeTaxReturnYearsAdmin)
