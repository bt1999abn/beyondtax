# Generated by Django 5.0.3 on 2024-07-03 20:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0014_residentialstatusanswer_income_tax'),
    ]

    operations = [
        migrations.AlterField(
            model_name='residentialstatusanswer',
            name='income_tax',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_answers', to='incomeTax.incometaxprofile'),
        ),
    ]
