# Generated by Django 5.0.3 on 2024-07-24 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0039_alter_businessincome_business_income_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessincome',
            name='industry',
            field=models.CharField(choices=[(1, 'Farming'), (2, 'Dairy'), (3, 'Fisheries'), (4, 'Textiles And Garments'), (5, 'Automobiles And Auto Components'), (6, 'Electronics'), (7, 'Pharmaceuticals'), (8, 'Chemicals'), (9, 'Clothing And Apparel'), (10, 'IT Services')]),
        ),
    ]
