from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# For automatically registering all the apps
from accounts import models as accounts_models


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
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
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
    list_display = ('email', 'first_name', 'last_name', 'is_superuser', 'date_of_birth', 'gender', 'mobile_number',
                    'is_active')
    list_filter = ('is_superuser',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'mobile_number')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'is_active', 'is_staff', 'is_superuser')
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


# Now register the new UserAdmin...
admin.site.register(accounts_models.User, UserAdmin)
# # ... and, since we're not using Django's built-in permissions,
# # unregister the Group model from admin_panel.
# admin_panel.site.unregister(Group)
