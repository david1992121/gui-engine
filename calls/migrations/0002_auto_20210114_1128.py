# Generated by Django 3.1.3 on 2021-01-14 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.IntegerField(choices=[(0, 'キャスト募集中'), (1, 'キャスト選択期間'), (2, '提案中'), (3, 'キャスト確定'), (4, '合流中'), (5, '合流完了'), (6, '完了（決済未完了）'), (7, '決済完了'), (8, 'キャスト不足でキャンセル'), (9, '運営側キャンセル'), (10, '一般なエラー')], default=0, verbose_name='状態'),
        ),
    ]
