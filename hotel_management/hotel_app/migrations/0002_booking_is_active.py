# Generated by Django 5.1.5 on 2025-01-29 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hotel_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
