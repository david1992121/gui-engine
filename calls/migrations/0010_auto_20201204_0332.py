# Generated by Django 3.1.3 on 2020-12-03 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0009_auto_20201130_0106'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='night_ended_at',
            field=models.TimeField(blank=True, null=True, verbose_name='深夜料利用修了'),
        ),
        migrations.AddField(
            model_name='order',
            name='night_fund',
            field=models.IntegerField(default=4000, verbose_name='深夜料'),
        ),
        migrations.AddField(
            model_name='order',
            name='night_started_at',
            field=models.TimeField(blank=True, null=True, verbose_name='深夜料利用開始'),
        ),
        migrations.AddField(
            model_name='order',
            name='operator_message',
            field=models.TextField(null=True, verbose_name='オペレーターメッセージ'),
        ),
    ]
