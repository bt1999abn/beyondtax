# Generated by Django 5.0.3 on 2024-07-30 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0044_alter_rentalincome_tenant_aadhar_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='capitalgains',
            name='term_type',
            field=models.IntegerField(choices=[(1, 'Short Term'), (2, 'Long Term')], null=True),
        ),
    ]
