# Generated by Django 5.1.2 on 2024-11-12 20:42

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('google_id', models.CharField(blank=True, max_length=255, null=True)),
                ('apple_id', models.CharField(blank=True, max_length=255, null=True)),
                ('full_name', models.CharField(max_length=100)),
                ('gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default='other', max_length=10)),
                ('age', models.PositiveIntegerField(blank=True, null=True)),
                ('photo_url', models.URLField(blank=True, max_length=255, null=True)),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('status', models.CharField(choices=[('verified', 'Verified'), ('unverified', 'Unverified')], default='unverified', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
