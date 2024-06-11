# Generated by Django 5.0.3 on 2024-06-11 11:55

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0054_alter_otprecord_otp_alter_user_mobile_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='mobile_number',
            field=models.CharField(blank=True, max_length=10, validators=[django.core.validators.RegexValidator(message='Phone number can be only 10 digits.', regex='^([1-9][0-9]{9})$')]),
        ),
    ]
