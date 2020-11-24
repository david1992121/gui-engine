from django.db import models
from accounts.models import Member
from basics.models import Location, CostPlan, Choice

# Create your models here.
class Order(models.Model):
    status = models.CharField('状態', null = True, blank = True, max_length = 50)
    reservation = models.CharField('予約名', null = True, blank = True, max_length = 100)
    place = models.CharField('予約場所', null=True, blank=True, max_length=100)
    user = models.ForeignKey(Member, related_name='orders', on_delete = models.SET_NULL, null = True, blank = True, verbose_name='オーダー')
    joined = models.ManyToManyField(Member, related_name = "applied", verbose_name="応募者")
    parent_location = models.ForeignKey(Location, related_name = "with_parent", on_delete = models.PROTECT, null = True, blank = True)
    meet_time = models.CharField("合流時間", default = "", max_length = 50)
    meet_time_iso = models.CharField("ISO時間", default = "", max_length = 50)
    time_other = models.BooleanField("他時間", default = False)
    location = models.ForeignKey(Location, related_name = "with_child", on_delete = models.PROTECT, null = True, blank = True)
    location_other = models.CharField('他の場所', null=True, blank =True, max_length=100)
    person = models.IntegerField('合流人数', default=1)
    period = models.IntegerField('合流時間', default=1)
    cost_plan = models.ForeignKey(CostPlan, on_delete = models.SET_NULL, null = True, blank = True)
    situations = models.ManyToManyField(Choice, verbose_name='気持ち', related_name = "with_choice")
    desired = models.ManyToManyField(Member, related_name = "invited", verbose_name="ご希望のキャスト")
    is_private = models.BooleanField('プライベート', default=False)

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