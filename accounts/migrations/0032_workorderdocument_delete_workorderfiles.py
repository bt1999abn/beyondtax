# Generated by Django 5.0.3 on 2024-04-23 14:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0031_alter_servicepages_required_documents'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrderDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_name', models.CharField(default='file name', max_length=255)),
                ('document_file', models.FileField(upload_to='work_order_document_files/')),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_order', to='accounts.workorder')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='WorkOrderFiles',
        ),
    ]
