# Generated by Django 5.1.2 on 2024-11-26 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('picplan', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='notify_overspent',
            field=models.BooleanField(default=False),
        ),
    ]
