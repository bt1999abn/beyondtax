# Generated by Django 5.0.3 on 2024-05-01 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0038_workorderdocument_uploaded_by_beyondtax'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='upcomingduedates',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='upcomingduedates',
            name='date',
        ),
        migrations.RemoveField(
            model_name='upcomingduedates',
            name='description',
        ),
        migrations.AddField(
            model_name='upcomingduedates',
            name='data',
            field=models.JSONField(default=dict),
        ),
    ]
