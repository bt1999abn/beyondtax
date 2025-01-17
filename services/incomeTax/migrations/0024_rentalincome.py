# Generated by Django 5.0.3 on 2024-07-18 03:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0023_salaryincome'),
    ]

    operations = [
        migrations.CreateModel(
            name='RentalIncome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('occupancy_status', models.IntegerField(choices=[(1, 'Let-out'), (2, 'Self-occupied')])),
                ('tenant_name', models.CharField(max_length=255)),
                ('tenant_aadhar', models.CharField(max_length=255)),
                ('tenant_pan', models.CharField(max_length=255)),
                ('property_door_no', models.CharField(max_length=255)),
                ('property_area', models.CharField(max_length=255)),
                ('property_city', models.CharField(max_length=255)),
                ('property_pincode', models.CharField(max_length=255)),
                ('property_state', models.CharField(max_length=255)),
                ('property_country', models.CharField(max_length=255)),
                ('annual_rent', models.DecimalField(decimal_places=2, max_digits=30)),
                ('property_tax_paid', models.DecimalField(decimal_places=2, max_digits=30)),
                ('standard_deduction', models.DecimalField(decimal_places=2, max_digits=30)),
                ('interest_on_home_loan_dcp', models.DecimalField(decimal_places=2, max_digits=30)),
                ('interest_on_home_loan_pc', models.DecimalField(decimal_places=2, max_digits=30)),
                ('net_rental_income', models.DecimalField(decimal_places=2, max_digits=30)),
                ('ownership_percent', models.IntegerField(max_length=3)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rental_incomes', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rental_incomes', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
