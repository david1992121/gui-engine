# Generated by Django 3.1.3 on 2020-11-07 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('basics', '0010_banner'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='ranking_display',
            field=models.BooleanField(default=True, verbose_name='ranking_display'),
        ),
    ]