from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django_resized.forms import ResizedImageField

# Create your models here.
class Setting(models.Model):

    ##### app setting #####
    app_footprint = models.BooleanField('app_footprint', default=True)       # gui use
    app_tweetlike = models.BooleanField('app_tweetlike', default=True)
    app_autodelay = models.BooleanField('app_autodelay', default=True)
    app_autocharge = models.BooleanField('app_autocharge', default=True)
    app_autoremove = models.BooleanField('app_autoremove', default=True)

    ##### ranking #####
    ranking_display = models.BooleanField('ranking_display', default = True) # gui use

    ##### email setting #####
    email_footprint = models.BooleanField('email_footprint', default=True)
    email_like = models.BooleanField('email_like', default=True)
    email_message = models.BooleanField('email_message', default=True)       # gui use
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
    order = models.IntegerField('順序', default=0)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)
    
class CastClass(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('名前', unique=True, max_length=190)
    en_name = models.CharField('英語名前', unique=True, null = True, blank = True, max_length=190)
    color = models.CharField('色', null = True, blank = True, max_length=190)
    point = models.IntegerField('しきい値', default=0)
    order = models.IntegerField('順序', default=0)
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

class Choice(models.Model):
    def __str__(self):
        return self.name
    
    CATEGORY_CHOICES = (
        ('s', 'situation'),
        ('r', 'request'),
        ('c', 'condition')
    )
    name = models.CharField('名称', max_length=100)
    category = models.CharField('カテゴリ', choices = CATEGORY_CHOICES, default = 's', max_length = 2)
    subcategory = models.CharField('サブカテゴリ', null = True, blank = True, max_length = 50)
    order = models.IntegerField('順序', default = 0)
    score = models.IntegerField('スコア', validators=[MinValueValidator(1), MaxValueValidator(100)], default = 5)
    call_shown = models.BooleanField('有効設定', default = True)
    cast_shown = models.BooleanField('キャスト表示', default = True)
    customer_shown = models.BooleanField('カスタマ項目', default = True)
    sub_one = models.BooleanField('サブカテゴリ内単一設定', default = False)

    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

class ReceiptSetting(models.Model):
    company_name = models.CharField('会社名', max_length = 100)
    postal_code = models.CharField('郵便', max_length=8) # validators=[RegexValidator(r'^\d\d\d-\d\d\d\d$')]
    address = models.CharField('住所', max_length=100)
    building = models.CharField('番地・建物名', max_length=100)
    phone_number = models.CharField('電話番号', max_length=15) # validators=[RegexValidator(r'^\d\d-\d\d\d\d-\d\d\d\d$')]
    charger = models.CharField('担当者名', max_length=20)

class Banner(models.Model):
    def __str__(self):
        return self.name

    CATEGORY_CHOICES = (
        ('u', '上表示'),
        ('m', '中表示'),
        ('d', '下表示'),
        ('n', '非表示'),
    )
    name = models.CharField('名称', max_length=100)
    banner_image = models.ImageField('バナー画像', null = True, blank = True, upload_to = "static/image")
    main_image = models.ImageField("メイン画像", null = True, blank = True, upload_to = "static/image")
    category = models.CharField('カテゴリ', choices = CATEGORY_CHOICES, default = 'u', max_length = 2)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

class Gift(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('名称', max_length=100)
    location = models.ForeignKey(Location, verbose_name='支店', on_delete=models.SET_NULL, null = True)
    image = ResizedImageField('URI',  size = [200, 200], crop=['middle', 'center'], null=True, blank=True, upload_to = "static/images", quality = 75)
    point = models.IntegerField('価格')
    back = models.IntegerField('バック値', default=0)
    is_shown = models.BooleanField('表示', default = True)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

class CostPlan(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('名称', max_length=100)
    location = models.ForeignKey(Location, verbose_name='支店', on_delete=models.SET_NULL, null = True)
    cost = models.IntegerField('料金')
    extend_cost = models.IntegerField('延長料金')
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)