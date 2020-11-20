# Generated by Django 3.1.3 on 2020-11-19 14:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0027_member_is_public'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('basics', '0013_auto_20201108_1601'),
        ('calls', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_group', models.BooleanField(default=False, verbose_name='グループ')),
                ('last_message', models.TextField(blank=True, null=True, verbose_name='最後のメッセージ')),
                ('room_type', models.CharField(blank=True, max_length=30, null=True, verbose_name='タイプ')),
                ('title', models.CharField(blank=True, max_length=130, null=True, verbose_name='タイトル')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('joins', models.ManyToManyField(related_name='joinings', to=settings.AUTH_USER_MODEL, verbose_name='合流者')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='calls.order')),
                ('users', models.ManyToManyField(related_name='rooms', to=settings.AUTH_USER_MODEL, verbose_name='メンバー')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, null=True, verbose_name='コンテンツ')),
                ('is_read', models.BooleanField(default=False, verbose_name='読み済み')),
                ('is_notice', models.BooleanField(default=False, verbose_name='通知')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('gift', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='basics.gift', verbose_name='ギフト')),
                ('medias', models.ManyToManyField(to='accounts.Media', verbose_name='画像')),
                ('receiver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received', to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.room', verbose_name='ルーム')),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sended', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]