from django.contrib import admin

from services.incomeTax.models import IncomeTaxBankDetails, IncomeTaxAddress, IncomeTaxProfile, IncomeTaxReturnYears, \
    IncomeTaxReturn, ResidentialStatusQuestions, ResidentialStatusAnswer


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


admin.site.register(IncomeTaxProfile, IncomeTaxProfileAdmin)
admin.site.register(IncomeTaxReturnYears, IncomeTaxReturnYearsAdmin)
admin.site.register(ResidentialStatusQuestions, ResidentialStatusAdmin)
admin.site.register(ResidentialStatusAnswer, ResidentialStatusAnswerAdmin)