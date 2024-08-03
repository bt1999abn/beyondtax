# Generated by Django 5.0.3 on 2024-07-18 04:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0027_agricultureincome_landdetails'),
    ]

    operations = [
        migrations.CreateModel(
            name='DividendIncome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('particular', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dividend_income', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dividend_income', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExemptIncome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('exempt_income_type', models.IntegerField(choices=[(1, 'Savings Bank A/c'), (2, 'Fixed deposits'), (3, 'others')])),
                ('description', models.CharField(max_length=255)),
                ('interest_amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exempt_incomes', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exempt_incomes', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExemptIncomeInAgriculture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('exemption_type', models.IntegerField(choices=[(1, 'Irrigated'), (2, 'NRE A/C'), (3, 'others')])),
                ('particular', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('interest_received', models.IntegerField(max_length=3)),
                ('interest_amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exempt_incomes_agriculture', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exempt_incomes_agriculture', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='IncomeFromBetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('particular', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='income_from_betting', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='income_from_betting', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InterestOnItRefunds',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('particular', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interest_on_it_refunds', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interest_on_it_refunds', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]