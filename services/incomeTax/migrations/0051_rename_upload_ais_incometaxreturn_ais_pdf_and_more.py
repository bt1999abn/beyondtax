# Generated by Django 5.0.3 on 2024-08-09 11:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0050_incometaxreturn_upload_26as_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='incometaxreturn',
            old_name='upload_ais',
            new_name='ais_pdf',
        ),
        migrations.RenameField(
            model_name='incometaxreturn',
            old_name='upload_26as',
            new_name='tds_pdf',
        ),
    ]