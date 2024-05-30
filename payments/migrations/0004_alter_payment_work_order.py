# Generated by Django 5.0.3 on 2024-05-28 12:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_alter_payment_status'),
        ('workOrder', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='work_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='work_order_payments', to='workOrder.workorder'),
        ),
    ]
