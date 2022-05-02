"""
Models for Chat
"""
from django.db import models
from django.db.models.fields import related
from accounts.models import Member, Media
from basics.models import Gift, Location


class Room(models.Model):
    """
    Room Model
    """

    ROOM_CHOICES = (
        (0, 'default'),
        (1, 'suggest'),  # not used
        (2, 'confirm'),
        (3, 'end')       # effective only groupchat
    )

    is_group = models.BooleanField('グループ', default=False)
    users = models.ManyToManyField(
        Member, related_name='rooms', verbose_name='メンバー')
    last_message = models.TextField('最後のメッセージ', null=True, blank=True)
    last_sender = models.ForeignKey(
        Member,
        related_name='last_rooms',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='最後投稿者')
    room_type = models.CharField('タイプ', default='', max_length=30)
    title = models.CharField('タイトル', null=True, blank=True, max_length=130)
    status = models.IntegerField('ステータス', choices=ROOM_CHOICES, default=0)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)


class Message(models.Model):
    """
    Message Model
    """
    content = models.TextField('コンテンツ', null=True, blank=True)
    medias = models.ManyToManyField(Media, verbose_name="画像")
    gift = models.ForeignKey(
        Gift, on_delete=models.SET_NULL, null=True, verbose_name='ギフト')
    is_read = models.BooleanField('読み済み', default=False)
    room = models.ForeignKey(
        Room,
        related_name="messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='ルーム')
    sender = models.ForeignKey(
        Member, related_name="sended", on_delete=models.SET_NULL, null=True)
    receiver = models.ForeignKey(
        Member, related_name="received", on_delete=models.SET_NULL, null=True)
    is_notice = models.BooleanField('通知', default=False)
    is_like = models.BooleanField('イイネ', default=False)
    follower = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        verbose_name="新メッセージ")

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

# class Suggestion(models.Model):
#     """
#     Suggestion Model
#     """
#     meet_at = models.DateTimeField('日程')
#     period = models.IntegerField('時間', default = 1)
#     address = models.ForeignKey(Location, on_delete = models.CASCADE, null = True)
#     point_half = models.IntegerField('時間単価')
#     is_cancelled = models.BooleanField('キャンセル', default = False)
#     is_accepted = models.BooleanField('OK', default = False)
#     is_replied = models.BooleanField('応答', default = False)
#     user = models.ForeignKey(Member, on_delete = models.SET_NULL, null = True, related_name = "suggested")
#     target = models.ForeignKey(Member, on_delete = models.SET_NULL, null = True, related_name = "asked")
#     room = models.ForeignKey(Room, on_delete = models.CASCADE, related_name = "suggestions")
#     created_at = models.DateTimeField('作成日時', auto_now_add=True)
#     updated_at = models.DateTimeField('更新日時', auto_now=True)


class Notice(models.Model):
    """
    Notice Model
    """
    content = models.CharField('内容', max_length=100, default="")
    user = models.ForeignKey(Member, related_name="rececived_notices",
                             on_delete=models.CASCADE, verbose_name="通知先")
    from_user = models.ForeignKey(
        Member,
        related_name="sent_notices",
        on_delete=models.CASCADE,
        verbose_name="通知元")
    notice_type = models.CharField('タイプ', default="foot", max_length=100)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)


class AdminNotice(models.Model):
    """
    AdminNotice Model
    """
    title = models.CharField('タイトル', default="", max_length=190)
    content = models.TextField('コンテンツ', null=True, blank=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='支店')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
