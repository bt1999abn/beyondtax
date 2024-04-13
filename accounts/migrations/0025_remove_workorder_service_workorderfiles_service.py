# Generated by Django 5.0.3 on 2024-04-13 13:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0024_remove_workorderfiles_service_workorder_service'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workorder',
            name='service',
        ),
        migrations.AddField(
            model_name='workorderfiles',
            name='service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work_order_files', to='accounts.servicepages'),
        ),
    ]
