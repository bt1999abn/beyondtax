# Generated by Django 5.0.3 on 2024-07-24 08:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0041_alter_businessincome_industry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deductions',
            name='income_tax_return',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='deductions', to='incomeTax.incometaxreturn'),
        ),
    ]