# Generated by Django 5.0.3 on 2024-07-03 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0011_remove_residentialstatus_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incometaxprofile',
            name='residential_status',
            field=models.IntegerField(blank=True, choices=[(1, 'Indian Resident'), (2, 'Non-Resident Indian'), (3, 'IndianResident(NotOrdinary)'), (3, 'IndianResident(Ordinary)')]),
        ),
    ]
