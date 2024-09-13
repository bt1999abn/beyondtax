# Generated by Django 5.0.3 on 2024-09-13 08:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0058_governmentid_profileaddress_profilebankaccounts_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profileaddress',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile_address', to=settings.AUTH_USER_MODEL),
        ),
    ]
