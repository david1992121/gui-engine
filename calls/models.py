from django.db import models
from django.utils import tree
from accounts.models import Member
from basics.models import Location, CostPlan, Choice
from django.core.validators import MaxValueValidator, MinValueValidator
from chat.models import Room

# Create your models here.
class Order(models.Model):

    STATUS_CHOICES = (
        (0, 'キャスト募集中'),
        (1, 'キャスト選択期間'),
        (2, '提案中'),
        (3, 'キャスト確定'),
        (4, '合流中'),
        (5, '合流完了'),
        (6, '完了（決済未完了'),
        (7, '決済完了'),
        (8, 'キャスト不足でキャンセル'),
        (9, '運営側キャンセル'),
        (10, '一般なエラー'),
    )
    status = models.IntegerField('状態', choices = STATUS_CHOICES, default = 0)
    reservation = models.CharField('予約名', null = True, blank = True, max_length = 100)
    place = models.CharField('予約場所', null=True, blank=True, max_length=100)
    user = models.ForeignKey(Member, related_name='orders', on_delete = models.SET_NULL, null = True, blank = True, verbose_name='オーダー')
    parent_location = models.ForeignKey(Location, related_name = "with_parent", on_delete = models.PROTECT, null = True, blank = True)
    meet_time = models.CharField("合流時間", default = "", max_length = 50)
    meet_time_iso = models.DateTimeField("ISO時間", null = True, blank = True)
    time_other = models.BooleanField("他時間", default = False)
    location = models.ForeignKey(Location, related_name = "with_child", on_delete = models.PROTECT, null = True, blank = True)
    location_other = models.CharField('他の場所', null=True, blank =True, max_length=100)
    person = models.IntegerField('合流人数', default=1)
    period = models.IntegerField('合流時間', default=1)
    cost_plan = models.ForeignKey(CostPlan, on_delete = models.SET_NULL, null = True, blank = True)
    situations = models.ManyToManyField(Choice, verbose_name='気持ち', related_name = "with_choice")
    is_private = models.BooleanField('プライベート', default=False)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, related_name = "orders", null=True, blank=True, verbose_name="チャットルーム")

    # collect started at
    collect_started_at = models.DateTimeField('キャスト募集開始時刻', null=True, blank=True)
    collect_ended_at = models.DateTimeField('キャスト募集修了時刻', null=True, blank=True)
    ended_predict = models.DateTimeField('修了予定時刻', null = True)
    ended_at = models.DateTimeField('修了時刻', null = True)

    # cost
    cost_value = models.IntegerField('料金', default = 0)
    cost_extended = models.IntegerField('延長料金', default = 0)
    final_cost = models.IntegerField('確定料金', default = 0)

    # message
    remark = models.TextField('備考', null = True)
    operator_message = models.TextField('オペレーターメッセージ', null = True)

    # night started at
    night_started_at = models.TimeField('深夜料利用開始', null = True, blank=True)
    night_ended_at = models.TimeField('深夜料利用修了', null = True, blank=True)
    night_fund = models.IntegerField('深夜料', default = 4000)
    night_back_ratio = models.IntegerField('深夜料バック率', default = 0)
    
    # desire cast
    desire_cost = models.IntegerField('指名料', default = 2000)
    desire_back_ratio = models.IntegerField('指名料バック率', default = 0)

    # private call
    target = models.ForeignKey(Member, on_delete=models.SET_NULL, null = True, related_name = "asked")
    is_cancelled = models.BooleanField('キャンセル', default = False)
    is_accepted = models.BooleanField('OK', default = False)
    is_replied = models.BooleanField('応答', default = False)    

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

class Invoice(models.Model):

    invoice_type = models.CharField('目的', null = True, blank = True, max_length=100)
    give_amount = models.IntegerField('ポイント', default = 0)
    take_amount = models.IntegerField('ポイント', default = 0)
    giver = models.ForeignKey(Member, on_delete = models.SET_NULL, related_name = "gave", null=True, verbose_name="使用")
    taker = models.ForeignKey(Member, on_delete=models.SET_NULL, related_name = "took", null=True, verbose_name="取得")
    order = models.ForeignKey(Order, on_delete = models.SET_NULL, null = True)
    reason = models.CharField('理由', default = "", max_length=190)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

class Join(models.Model):
    """
    Join Model
    """

    SELECT_CHOICES = (
        (0, 'キャスト募集'),
        (1, '優先マッチング')        
    )

    STATUS_CHOICES = (
        (0, 'ドラフト'),
        (1, '確定'),        
    )

    user = models.ForeignKey(Member, related_name = "joins", on_delete = models.SET_NULL, null = True, verbose_name="ユーザー")
    order = models.ForeignKey(Order, related_name = "joins", on_delete = models.SET_NULL, null = True, verbose_name="チャットルーム")
    started_at = models.DateTimeField("開始時間", null = True)
    ended_at = models.DateTimeField("修了時間", null = True)
    status = models.IntegerField('状態', choices = STATUS_CHOICES, default = 0)
    selection = models.IntegerField('選択', choices = SELECT_CHOICES, default = 0)
    dropped = models.BooleanField('却下', default = False)

    is_started = models.BooleanField("開始", default = False)
    is_ten_left = models.BooleanField("10分前", default = False)
    is_extended = models.BooleanField("延長", default = False)
    is_ended = models.BooleanField("修了", default = False)

class Review(models.Model):
    source = models.ForeignKey(Member, on_delete=models.SET_NULL, null = True, blank = True, related_name='review_targets', verbose_name='レビュー元')
    target = models.ForeignKey(Member, on_delete=models.SET_NULL, null = True, blank = True, related_name='review_sources', verbose_name='レビュー先')
    stars = models.IntegerField('スター', default = 5, validators=[MaxValueValidator(5),  MinValueValidator(1)])
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null = True, verbose_name="オーダー", related_name = "reviews")
    content = models.TextField('内容', null = True, blank = True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
