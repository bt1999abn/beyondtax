from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts import models as accounts_models
from accounts.models import UpcomingDueDates, OtpRecord, ProfileInformation, ProfileAddress, ProfileBankAccounts, \
    GovernmentID, FinancialOwnershipDetails, UnlistedShareHolding, DirectorshipDetails, EsopDetails, \
    ReturnFilingInformation
from accounts.proxy_models import ProductProxy
from payments.models import Payment


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = accounts_models.User
        fields = ('email', 'first_name', 'last_name', 'date_of_birth', 'mobile_number')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin_panel's
    password hash display field.
    """
    class Meta:
        model = accounts_models.User
        fields = ('email', 'password', 'first_name', 'last_name', 'date_of_birth', 'gender', 'mobile_number',
                  'is_active', "user_permissions", "groups")

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    # form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('mobile_number', 'email', 'first_name', 'last_name', 'is_superuser', 'date_of_birth', 'gender',
                    'is_active')
    list_filter = ('is_superuser',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'mobile_number')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'is_active', 'is_staff', 'is_superuser','client_type',
                       'industry_type', 'nature_of_business', 'business_name', 'business_mobile_number', 'business_email',
                       'contact_person', 'job_title', 'contact_person_phone_number', 'contact_email', 'date_of_formation',
                       'annual_revenue', 'number_of_employees')
        }),
        ('Permissions', {'fields': ('user_permissions', "groups")}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'date_of_birth', 'gender', 'mobile_number', 'password1',
                       'password2', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ("user_permissions",)


class ProfileInformationAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'fathers_name', 'date_of_birth', 'gender', 'maritual_status')
    search_fields = ('user__mobile_number', 'first_name', 'last_name', 'fathers_name')
    list_filter = ('gender', 'maritual_status')


class ProfileAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_type', 'rent_status', 'door_no', 'street', 'city', 'state', 'pincode', 'country')
    search_fields = ('user__mobile_number', 'door_no', 'city', 'state', 'pincode')
    list_filter = ('address_type', 'rent_status', 'state', 'country')


class ProfileBankAccountsAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_no', 'bank_name', 'ifsc_code', 'type', 'is_primary')
    search_fields = ('user__mobile_number', 'account_no', 'bank_name', 'ifsc_code')
    list_filter = ('type', 'is_primary')


class GovernmentIDAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'pan_no', 'is_pan_verified', 'aadhar_no', 'is_aadhaar_verified', 'driving_license_no',
        'is_driving_license_verified', 'voter_id_no', 'is_voter_id_verified', 'ration_card_no',
        'is_ration_card_verified', 'passport_no', 'is_passport_verified'
    )
    search_fields = ('user__mobile_number', 'pan_no', 'aadhar_no', 'driving_license_no', 'voter_id_no', 'ration_card_no', 'passport_no')
    list_filter = ('is_pan_verified', 'is_aadhaar_verified', 'is_driving_license_verified', 'is_voter_id_verified', 'is_ration_card_verified', 'is_passport_verified')


class ProductProxyAdmin(admin.ModelAdmin):

    list_display = ('product_name', 'amount', 'discount', 'government_fee', 'due_date', 'due_duration')
    list_filter = ('category', 'client_type', 'frequency')


class UpcomingDueDateAdmin(admin.ModelAdmin):
    list_display = ('date', 'compliance_activity', 'service_type', 'penalty_fine_interest')
    list_filter = ('service_type',)
    search_fields = ('compliance_activity', 'service_type')


class OtpRecordAdmin(admin.ModelAdmin):
    list_display = ('email', 'mobile_number', 'otp', 'created_at', 'source')
    list_filter = ('source',)
    search_fields = ('source',)


class FinancialOwnershipDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_partner_in_firm', 'has_unlisted_shares', 'is_director_in_company', 'has_esops')
    search_fields = ('user__username',)
    list_filter = ('is_partner_in_firm', 'has_unlisted_shares', 'is_director_in_company', 'has_esops')


class UnlistedShareHoldingAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'pan_of_company', 'company_type')
    search_fields = ('company_name', 'pan_of_company')
    list_filter = ('company_type',)


class DirectorshipDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'pan_of_company', 'company_type')
    search_fields = ('company_name', 'pan_of_company')
    list_filter = ('company_type',)


class EsopDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'startup_name', 'pan_of_company', 'dpit_reg_no')
    search_fields = ('startup_name', 'pan_of_company', 'dpit_reg_no')


class ReturnFilingInformationAdmin(admin.ModelAdmin):
    list_display = ('user', 'section_filed_under', 'return_type', 'has_representative_access')
    search_fields = ('section_filed_under', 'return_type')
    list_filter = ('section_filed_under', 'return_type')


# Now register the new UserAdmin...
admin.site.register(accounts_models.User, UserAdmin)
admin.site.register(ProductProxy, ProductProxyAdmin)
admin.site.register(UpcomingDueDates, UpcomingDueDateAdmin)
admin.site.register(OtpRecord, OtpRecordAdmin)
admin.site.register(ProfileInformation, ProfileInformationAdmin)
admin.site.register(ProfileAddress, ProfileAddressAdmin)
admin.site.register(ProfileBankAccounts, ProfileBankAccountsAdmin)
admin.site.register(GovernmentID, GovernmentIDAdmin)
admin.site.register(FinancialOwnershipDetails, FinancialOwnershipDetailsAdmin)
admin.site.register(UnlistedShareHolding, UnlistedShareHoldingAdmin)
admin.site.register(DirectorshipDetails, DirectorshipDetailsAdmin)
admin.site.register(EsopDetails, EsopDetailsAdmin)
admin.site.register(ReturnFilingInformation, ReturnFilingInformationAdmin)
# # ... and, since we're not using Django's built-in permissions,
# # unregister the Group model from admin_panel.
# admin_panel.site.unregister(Group)
