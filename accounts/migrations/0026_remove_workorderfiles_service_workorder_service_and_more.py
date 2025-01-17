# Generated by Django 5.0.3 on 2024-04-13 17:39

import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0025_remove_workorder_service_workorderfiles_service'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workorderfiles',
            name='service',
        ),
        migrations.AddField(
            model_name='workorder',
            name='service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work_order_files', to='accounts.servicepages'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='status',
            field=models.IntegerField(choices=[(1, 'Inprocess'), (2, 'Available'), (3, 'Canceled')], default=1, null=True),
        ),
        migrations.AlterField(
            model_name='workorderfiles',
            name='work_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_order', to='accounts.workorder'),
        ),
    ]
