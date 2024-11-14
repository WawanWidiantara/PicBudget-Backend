# Generated by Django 5.1.2 on 2024-11-14 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_transaction_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='method',
            field=models.CharField(choices=[('manual', 'Manual'), ('picscan', 'PicScan'), ('picvoice', 'PicVoice')], default='manual', max_length=10),
        ),
        migrations.AddField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='confirmed', max_length=10),
        ),
    ]