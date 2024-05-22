# Generated by Django 5.0.3 on 2024-05-21 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0052_alter_upcomingduedates_department'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upcomingduedates',
            name='department',
            field=models.IntegerField(blank=True, choices=[(1, 'Business Essentials'), (2, 'Tax Related'), (3, 'Entity Formation'), (4, 'Income Tax'), (5, 'GST'), (6, 'Accounting'), (7, 'Company Compliance'), (8, 'TDS')], null=True),
        ),
    ]
