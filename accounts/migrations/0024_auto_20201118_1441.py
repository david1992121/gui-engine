# Generated by Django 3.1.3 on 2020-11-18 06:41

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_auto_20201117_0411'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='back_ratio',
            field=models.IntegerField(blank=True, null=True, verbose_name='バック率'),
        ),
        migrations.AddField(
            model_name='member',
            name='expire_amount',
            field=models.IntegerField(default=0, verbose_name='延長時間'),
        ),
        migrations.AddField(
            model_name='member',
            name='expire_times',
            field=models.IntegerField(default=0, verbose_name='延長回数'),
        ),
        migrations.AddField(
            model_name='member',
            name='memo',
            field=models.CharField(default='', max_length=190, verbose_name='メモ'),
        ),
        migrations.AlterUniqueTogether(
            name='favoritetweet',
            unique_together={('liker', 'tweet')},
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stars', models.IntegerField(default=5, validators=[django.core.validators.MaxValueValidator(5), django.core.validators.MinValueValidator(1)], verbose_name='スター')),
                ('content', models.TextField(blank=True, null=True, verbose_name='内容')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_targets', to=settings.AUTH_USER_MODEL, verbose_name='レビュー元')),
                ('target', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_sources', to=settings.AUTH_USER_MODEL, verbose_name='レビュー先')),
            ],
        ),
        migrations.CreateModel(
            name='Friendship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('favorite', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to=settings.AUTH_USER_MODEL, verbose_name='イイネ先')),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='イイネ元')),
            ],
            options={
                'verbose_name': 'フォロー関係',
                'verbose_name_plural': 'フォロー関係',
                'unique_together': {('follower', 'favorite')},
            },
        ),
    ]
