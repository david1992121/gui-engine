from re import T
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import related
from django_resized import ResizedImageField
from django.core.validators import MaxValueValidator, MinValueValidator
from .softmodels import SoftDeletionModel
from basics.models import Setting, CastClass, GuestLevel, Location, Choice

# Create your models here.
class Media(models.Model):
    def __str__(self):
        return self.uri.url
   
    uri = ResizedImageField('URI',  size = [400, 400], crop=['middle', 'center'], null=True, blank=True, upload_to = "static/images", quality = 75)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

class Detail(models.Model):
    
    QUALIFICATION_CHOICES = (
        (0, '未定'),
        (1, '中卒'),
        (2, '高卒'),
        (3, '大卒'),
        (4, '大学院卒'),
        (5, '専門卒'),
        (6, 'その他'),
    )

    ANNUAL_CHOICES = (
        (0, '未定'),
        (1, '500万以下'),
        (2, '500万～1000万'),
        (3, '1000万～1500万'),
        (4, '1500万～2000万'),
        (5, '2000万～3000万'),
        (6, '3000万～5000万'),
        (7, '5000万～1億'),
        (8, '1億以上'),
    )
    
    GUEST_STYLE_CHOICES = (
        (0, '未定'),
        (1, '細身'),
        (2, '普通'),
        (3, 'ガッチリ'),
        (4, 'ぽっちゃり'),
        (5, '太め'),
    )

    CAST_STYLE_CHOICES = (
        (0, '未定'),
        (1, '細身'),
        (2, '普通'),
        (3, 'グラマラス'),
    )

    # 自己紹介    
    about = models.TextField('自己紹介', default = "", null=True, blank=True)

    # 基本情報
    residence = models.CharField('居住地', default = "", null=True, blank=True, max_length = 100)
    birthplace = models.CharField('出身地', default = "", null=True, blank=True, max_length = 100)
    qualification = models.IntegerField('学歴', choices = QUALIFICATION_CHOICES, default = 0)
    annual = models.IntegerField('学歴', choices = ANNUAL_CHOICES, default = 0)
    job = models.CharField('お仕事', default = "", null=True, blank=True, max_length = 100)
    favorite = models.CharField('よく飲む地域', default = "", null=True, blank=True, max_length=100)
    drink = models.CharField('お酒', default = "", null=True, blank=True, max_length=100)
    smoke = models.CharField('タバコ', default = "", null=True, blank=True, max_length=100)
    sibling = models.CharField('兄弟姉妹', default = "", null=True, blank=True, max_length=100)  # cast only
    housemate = models.CharField('同居人', default = "", null=True, blank=True, max_length=100) # cast only
    language = models.CharField('外国語', default = "", null=True, blank=True, max_length=100)

    # 外見
    height = models.CharField('身長', default = "", null=True, blank=True, max_length = 3)
    guest_style = models.IntegerField('ゲストスタイル', choices = GUEST_STYLE_CHOICES, default = 0) # guest only
    cast_style = models.IntegerField('キャストスタイル', choices = CAST_STYLE_CHOICES, default = 0) # cast only
    hair = models.CharField('髪色・髪型', default = "", null=True, blank=True, max_length=100)
    entertainment = models.CharField('似ている芸能人', default = "", null=True, blank=True, max_length=100)
    charm = models.CharField('チャームポイント', default = "", null=True, blank=True, max_length=100)

    # 好みのタイプ　guest only
    girl_type = models.CharField('好きな女性のタイプ', default = "", null=True, blank=True, max_length=100)
    costume = models.CharField('好きな服装', default = "", null=True, blank=True, max_length=100)
    dislike = models.CharField('こういうタイプはNG', default = "", null=True, blank=True, max_length=100)

    # 性格　cast only
    character = models.CharField('性格', default = "", null=True, blank=True, max_length=100)

    # お話 cast only
    talk_type = models.CharField('話し上手？聞き上手？', default = "", null=True, blank=True, max_length=100)
    want_type = models.CharField('こんな話を話したい・聞きたい', default = "", null=True, blank=True, max_length=100)

class Member(SoftDeletionModel):
    def __str__(self):
        return self.username if self.username else "Undefined"

    SOCIAL_CHOICES = (
        (0, 'email'),
        (1, 'line'),
        (2, 'phone')
    )

    ROLE_CHOICES = (
        (-1, 'admin'),
        (0, 'cast'),
        (1, 'guest'),
        (10, 'applier')
    )

    ##### initial information #####
    email = models.EmailField('メールアドレス', unique=True, null=True, blank=True, max_length=100)
    social_type = models.IntegerField('ソーシャルタイプ', choices = SOCIAL_CHOICES, default = 0)
    social_id = models.CharField('ソーシャルID', null=True, blank=True, max_length=100)
    phone_number = models.CharField('電話番号', unique=True, null=True, blank=True, max_length=20)
    nickname = models.CharField('ニックネーム', unique = True, null = True, blank = True, max_length=190)
    avatars = models.ManyToManyField(Media, related_name="avatar", verbose_name='アバタ')
    is_registered = models.BooleanField('初期登録', default = False)
    is_verified = models.BooleanField('メール確認', default = False)

    ##### private info #####
    verify_code = models.CharField('認証コード', null=True, blank=True, max_length=100)
    birthday = models.DateTimeField('誕生日', null=True, blank=True)
    word = models.CharField('今日のひとこと', default = "", max_length=190)
    point = models.IntegerField('ポイント', default = 0)
    role = models.IntegerField('ユーザーロール', choices = ROLE_CHOICES, default = 1)
    status = models.BooleanField('オンライン', default=False)
    left_at = models.DateTimeField('オフライン日時', null=True, blank=True)
    setting = models.ForeignKey(Setting, on_delete=models.SET_NULL, null=True, blank=True)
    detail = models.ForeignKey(Detail, on_delete=models.SET_NULL, null=True, blank=True)
    is_joining = models.BooleanField('合流中', default=False)
    introducer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='intros', verbose_name='紹介者')

    ##### guest info #####
    point_used = models.IntegerField('利用ポイント', default = 0, validators=[MinValueValidator(0)])
    guest_level = models.ForeignKey(GuestLevel, on_delete=models.SET_NULL, null=True, blank=True)
    call_times = models.IntegerField('合流利用回数', default=0)
    guest_started_at = models.DateTimeField('ゲスト登録日時', null=True, blank=True)

    ##### cast info #####
    point_half = models.IntegerField('30分あたりのポイント', default = 3000, validators=[MaxValueValidator(100000),  MinValueValidator(1000)])
    video_point_half = models.IntegerField('ビデオオーダー料金', default = 3000, validators=[MaxValueValidator(100000),  MinValueValidator(1000)])
    is_applied = models.BooleanField('キャスト応募', default=False)
    is_present = models.BooleanField('出勤', default = False)
    presented_at = models.DateTimeField('出勤日時', null=True)
    cast_status = models.ManyToManyField(Choice, verbose_name='ステータス')
    cast_class = models.ForeignKey(CastClass, on_delete=models.SET_NULL, null=True, blank=True)
    cast_started_at = models.DateTimeField('キャスト登録日時', null=True, blank=True)

    ##### card and bank #####
    axes_exist = models.BooleanField('クレカ登録', default=False)

    ##### admin location ####
    location = models.ForeignKey(Location, on_delete = models.SET_NULL, null = True, blank = True, verbose_name='地域')

    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)
    
    REQUIRED_FIELDS = ['email']

    def save(self, *args, **kwargs):
        isNewOne = self.pk == None
        if isNewOne:
            new_detail = Detail.objects.create()
            new_setting = Setting.objects.create()
            self.detail = new_detail
            self.setting = new_setting
        
        instance = super(Member, self).save(*args, **kwargs)
        return instance
            
    class Meta:
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
        unique_together = ('social_type', 'social_id')

class TransferInfo(models.Model):

    ACCOUNT_TYPES = (
        (0, '通常'),
        (1, '当座'),        
    )

    bank_name = models.CharField('銀行名', default = "", max_length = 190)
    bank_no = models.CharField('金融機関番号', default = "", max_length = 190)
    site_name = models.CharField('支店名', default = "", max_length = 190)
    site_no = models.CharField('支店番号', default = "", max_length = 190)
    account_no = models.CharField('口座番号', default = "", max_length = 190)
    account_cat = models.IntegerField('口座種別', choices = ACCOUNT_TYPES, default = 0)
    transfer_name = models.CharField('名義', default = "", max_length=190)
    user = models.ForeignKey(Member, related_name = "transfer_infos", verbose_name='ユーザー', on_delete=models.SET_NULL, null=True, blank = True)

class TransferApplication(models.Model):

    STATUS_TYPES = (
        (0, '未処理'),
        (1, '処理済み')
    )

    APPLY_TYPES = (
        (0, '通常入金'),
        (1, 'すぐ入金')
    )

    status = models.IntegerField('ステータス', choices = STATUS_TYPES, default = 0)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null = True, blank=True, verbose_name='支店')
    user = models.ForeignKey(Member, related_name='transfer_applications', on_delete = models.SET_NULL, null = True, verbose_name='対象者')
    amount = models.IntegerField('現金', default=0)
    apply_type = models.IntegerField('種別', choices = APPLY_TYPES,)
    currency_type = models.CharField('通貨種別', default = "", max_length=190)
    point = models.IntegerField('ポイント', default = 0)
    created_at = models.DateTimeField('申請日時', auto_now_add = True)

class Tweet(models.Model):
    def __str__(self):
        return self.title

    CATEGORY_CHOICES = (
        (0, '全て'),
        (1, 'キャストのみ'),
    )
    content = models.TextField('内容', null = True, blank = True)
    images = models.ManyToManyField(Media, verbose_name='画像')
    user = models.ForeignKey(Member, on_delete = models.SET_NULL, null = True, blank = True)
    category = models.IntegerField('キャストのみ', choices = CATEGORY_CHOICES, default = 0)
    created_at = models.DateTimeField('作成日時', auto_now_add = True)
    updated_at = models.DateTimeField('更新日時', auto_now = True)

# Like Model
class FavoriteTweet(models.Model):
    def __unicode__(self):
        return self.name()

    liker = models.ForeignKey(Member, on_delete = models.SET_NULL, null = True, related_name="tweet_favorites", verbose_name="ユーザー")
    tweet = models.ForeignKey(Tweet, on_delete = models.SET_NULL, null = True, related_name="tweet_likers", verbose_name="つぶやき")
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    def name(self):
        return str(self.liker) + "💖" + self.favorite.title + "(" + str(self.favorite.creator) + ")"

    name.short_description = "名称"
    name.tags_allowed = True

    class Meta:
        verbose_name = "つぶやき-イイネ関係"
        verbose_name_plural = "つぶやき-イイネ関係"
