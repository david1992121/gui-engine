# Generated by Django 3.1.3 on 2020-12-11 15:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0018_join_is_ten_left'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='desired',
        ),
    ]