# Generated by Django 5.0.3 on 2024-07-18 04:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0028_dividendincome_exemptincome_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Deductions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('life_insurance', models.DecimalField(decimal_places=2, max_digits=30)),
                ('provident_fund', models.DecimalField(decimal_places=2, max_digits=30)),
                ('elss_mutual_fund', models.DecimalField(decimal_places=2, max_digits=30)),
                ('home_loan_repayment', models.DecimalField(decimal_places=2, max_digits=30)),
                ('tution_fees', models.DecimalField(decimal_places=2, max_digits=30)),
                ('stamp_duty_paid', models.DecimalField(decimal_places=2, max_digits=30)),
                ('others', models.DecimalField(decimal_places=2, max_digits=30)),
                ('contribution_by_self', models.DecimalField(decimal_places=2, max_digits=30)),
                ('contribution_by_employeer', models.DecimalField(decimal_places=2, max_digits=30)),
                ('medical_insurance_self', models.DecimalField(decimal_places=2, max_digits=30)),
                ('medical_preventive_health_checkup_self', models.DecimalField(decimal_places=2, max_digits=30)),
                ('medical_expenditure_self', models.DecimalField(decimal_places=2, max_digits=30)),
                ('senior_citizen_self', models.BooleanField()),
                ('medical_insurance_parents', models.DecimalField(decimal_places=2, max_digits=30)),
                ('medical_preventive_health_checkup_parents', models.DecimalField(decimal_places=2, max_digits=30)),
                ('medical_expenditure_parents', models.DecimalField(decimal_places=2, max_digits=30)),
                ('senior_citizen_parents', models.BooleanField()),
                ('education_loan', models.DecimalField(decimal_places=2, max_digits=30)),
                ('electronic_vehicle_loan', models.DecimalField(decimal_places=2, max_digits=30)),
                ('home_loan_taken_year', models.IntegerField(choices=[('Taken b/w Apr’16 - Mar’17', 'Taken b/w Apr’16 - Mar’17'), ('Taken b/w Apr’19 - Mar’22', 'Taken b/w Apr’19 - Mar’22')])),
                ('home_loan_amount', models.DecimalField(decimal_places=2, max_digits=30)),
                ('interest_income', models.DecimalField(decimal_places=2, max_digits=30)),
                ('royality_on_books', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_on_patients', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_on_bio_degradable', models.DecimalField(decimal_places=2, max_digits=30)),
                ('rent_paid', models.DecimalField(decimal_places=2, max_digits=30)),
                ('contribution_to_agnipath', models.DecimalField(decimal_places=2, max_digits=30)),
                ('donation_to_political_parties', models.DecimalField(decimal_places=2, max_digits=30)),
                ('donation_others', models.DecimalField(decimal_places=2, max_digits=30)),
                ('income_tax', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deductions', to='incomeTax.incometaxprofile')),
                ('income_tax_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deductions', to='incomeTax.incometaxreturn')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
