from django.db import models
from accounts.models import Member, Media
from calls.models import Order
from basics.models import Gift
class Room(models.Model):
    is_group = models.BooleanField('グループ', default = False)
    users = models.ManyToManyField(Member, related_name="rooms", verbose_name="メンバー")
    last_message = models.TextField('最後のメッセージ', null = True, blank = True)
    room_type = models.CharField('タイプ', null = True, blank=True, max_length=30)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null = True, blank= True)
    title = models.CharField('タイトル', null = True, blank= True, max_length=130)
    joins = models.ManyToManyField(Member, verbose_name="合流者", related_name = "joinings")

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

class Message(models.Model):
    content = models.TextField('コンテンツ', null=True, blank=True)
    medias = models.ManyToManyField(Media, verbose_name="画像")
    gift = models.ForeignKey(Gift, on_delete = models.SET_NULL, null = True, verbose_name='ギフト')
    is_read = models.BooleanField('読み済み', default = False)
    room = models.ForeignKey(Room, related_name="messages", on_delete = models.CASCADE, null = True, blank = True, verbose_name='ルーム')
    sender = models.ForeignKey(Member, related_name = "sended", on_delete = models.SET_NULL, null = True)
    receiver = models.ForeignKey(Member, related_name = "received", on_delete = models.SET_NULL, null = True)
    is_notice = models.BooleanField('通知', default = False)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
