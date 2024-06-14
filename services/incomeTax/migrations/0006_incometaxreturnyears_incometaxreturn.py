# Generated by Django 5.0.3 on 2024-06-13 16:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0005_alter_incometaxaddress_income_tax'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomeTaxReturnYears',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('due_date', models.DateField()),
                ('status', models.IntegerField(blank=True, choices=[(1, 'open'), (2, 'closed')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='IncomeTaxReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.IntegerField(blank=True, choices=[(1, 'Not Filed'), (2, 'Partially Filed'), (3, 'Filed')], default=1)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='income_tax_returns', to=settings.AUTH_USER_MODEL)),
                ('income_tax_return_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='income_tax_return_year', to='incomeTax.incometaxreturnyears')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
