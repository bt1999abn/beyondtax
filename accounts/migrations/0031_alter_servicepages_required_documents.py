# Generated by Django 5.0.3 on 2024-04-23 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_productproxy_servicepages_amount_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicepages',
            name='required_documents',
            field=models.CharField(max_length=255),
        ),
    ]
