from django.db import models

# Create your models here.
class Setting(models.Model):

    ##### app setting #####
    app_footprint = models.BooleanField('app_footprint', default=True)
    app_tweetlike = models.BooleanField('app_tweetlike', default=True)
    app_autodelay = models.BooleanField('app_autodelay', default=True)
    app_autocharge = models.BooleanField('app_autocharge', default=True)
    app_autoremove = models.BooleanField('app_autoremove', default=True)

    ##### email setting #####
    email_footprint = models.BooleanField('email_footprint', default=True)
    email_like = models.BooleanField('email_like', default=True)
    email_message = models.BooleanField('email_message', default=True)
    email_admin = models.BooleanField('email_admin', default=True)
    email_join_leave = models.BooleanField('email_join_leave', default=True)
    email_auto_delay = models.BooleanField('email_auto_delay', default=True)
    email_tweet_like = models.BooleanField('email_tweet_like', default=True)
    email_auto_charge = models.BooleanField('email_auto_charge', default=True)
    email_auto_remove = models.BooleanField('email_auto_remove', default=True)

    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

class GuestLevel(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('名前', unique=True, max_length=190)
    en_name = models.CharField('名前', unique=True, null = True, blank = True, max_length=190)
    point = models.IntegerField('しきい値', default=0)
    color = models.CharField('色', null = True, blank = True, max_length=190)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

    
class CastClass(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('名前', unique=True, max_length=190)
    en_name = models.CharField('英語名前', unique=True, null = True, blank = True, max_length=190)
    color = models.CharField('色', null = True, blank = True, max_length=190)
    point = models.IntegerField('しきい値', default=0)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

class Location(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('エリア', max_length=190)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, verbose_name='親エリア', null = True, blank = True)
    shown = models.BooleanField('表示', default = False)
    order = models.IntegerField('順序', default = 0)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)