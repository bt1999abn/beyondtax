# Generated by Django 5.0.3 on 2024-06-14 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_alter_user_mobile_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otprecord',
            name='otp_session_id',
            field=models.CharField(max_length=255),
        ),
    ]
