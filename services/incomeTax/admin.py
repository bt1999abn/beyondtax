from django.contrib import admin

from services.incomeTax.models import IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxProfile


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


admin.site.register(IncomeTaxProfile, IncomeTaxProfileAdmin)