# Generated by Django 3.1.3 on 2020-12-04 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0014_auto_20201205_0341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='join',
            name='ended_at',
            field=models.DateTimeField(null=True, verbose_name='修了時間'),
        ),
        migrations.AlterField(
            model_name='join',
            name='started_at',
            field=models.DateTimeField(null=True, verbose_name='開始時間'),
        ),
    ]