# Generated by Django 5.0.3 on 2024-05-15 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='screen_shot',
            field=models.ImageField(null=True, upload_to='payment_ss_upload_path/'),
        ),
    ]
