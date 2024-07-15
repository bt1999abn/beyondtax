# Generated by Django 5.0.3 on 2024-07-03 18:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0012_alter_incometaxprofile_residential_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='residentialstatus',
            name='context',
        ),
        migrations.RemoveField(
            model_name='residentialstatus',
            name='income_tax_profile',
        ),
        migrations.AlterField(
            model_name='incometaxprofile',
            name='residential_status',
            field=models.IntegerField(blank=True, choices=[(1, 'Indian Resident'), (2, 'Non-Resident Indian'), (3, 'IndianResident(NotOrdinary)'), (4, 'IndianResident(Ordinary)')]),
        ),
        migrations.CreateModel(
            name='ResidentialStatusAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('answer_text', models.CharField(max_length=255)),
                ('next_question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='previous_answers', to='incomeTax.residentialstatus')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='incomeTax.residentialstatus')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]