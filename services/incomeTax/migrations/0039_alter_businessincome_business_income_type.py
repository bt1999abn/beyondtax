# Generated by Django 5.0.3 on 2024-07-24 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0038_merge_20240722_2331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessincome',
            name='business_income_type',
            field=models.CharField(choices=[('44AD', '44AD'), ('44ADA', '44ADA')]),
        ),
    ]
