# Generated by Django 5.0.3 on 2024-05-28 12:58

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0043_remove_workorder_service_remove_workorder_user_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('service_name', models.CharField(max_length=255)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, null=True)),
                ('status', models.IntegerField(choices=[(1, 'Requested'), (2, 'Upload'), (3, 'Inprocess'), (4, 'Pay'), (5, 'Download')], default=1, null=True)),
                ('wo_dept', models.CharField(blank=True, max_length=255)),
                ('requested_by', models.CharField(blank=True, max_length=255)),
                ('client_id', models.IntegerField(blank=True, null=True)),
                ('client_type', models.CharField(blank=True, max_length=255)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('frequency', models.CharField(blank=True, max_length=255)),
                ('schedule_date', models.DateField(blank=True, null=True)),
                ('schedule_time', models.TimeField(blank=True, null=True)),
                ('started_on', models.DateTimeField(blank=True, null=True)),
                ('ended_on', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('service', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work_order_files', to='accounts.servicepages')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkOrderDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_name', models.CharField(default='file name', max_length=255)),
                ('document_file', models.FileField(upload_to='work_order_document_files/')),
                ('uploaded_by_beyondtax', models.BooleanField(default=False)),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_order', to='workOrder.workorder')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkOrderDownloadDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('download_document', models.FileField(upload_to='work_order_download_documents/')),
                ('description', models.CharField(blank=True, max_length=255)),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workOrder.workorder')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkorderPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank_account', models.CharField(max_length=255)),
                ('ifsc_code', models.CharField(max_length=11)),
                ('recipient_name', models.CharField(max_length=255)),
                ('qr_code_url', models.URLField()),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=10)),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='workOrder.workorder')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
