# Generated by Django 3.1.3 on 2020-12-15 15:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('basics', '0013_auto_20201108_1601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptsetting',
            name='postal_code',
            field=models.CharField(max_length=8, validators=[django.core.validators.RegexValidator('^\\d\\d\\d-\\d\\d\\d\\d$')], verbose_name='郵便'),
        ),
    ]
