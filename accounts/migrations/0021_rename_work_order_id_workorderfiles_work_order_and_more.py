# Generated by Django 5.0.3 on 2024-04-11 16:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_workorderfiles_file_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workorderfiles',
            old_name='work_order_id',
            new_name='work_order',
        ),
        migrations.AlterField(
            model_name='workorderfiles',
            name='service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work_order_files', to='accounts.servicepages'),
        ),
    ]
