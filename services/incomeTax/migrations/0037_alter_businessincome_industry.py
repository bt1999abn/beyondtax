# Generated by Django 5.0.3 on 2024-07-22 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomeTax', '0036_alter_buyerdetails_percentage_of_ownership_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessincome',
            name='industry',
            field=models.IntegerField(choices=[(1, 'Farming'), (2, 'Dairy'), (3, 'Fisheries'), (4, 'Textiles And Garments'), (5, 'Automobiles And Auto Components'), (6, 'Electronics'), (7, 'Pharmaceuticals'), (8, 'Chemicals'), (9, 'Clothing And Apparel'), (10, 'IT Services')]),
        ),
    ]