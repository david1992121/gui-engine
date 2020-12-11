from __future__ import absolute_import, unicode_literals

from .models import Order, Join
from accounts.models import Member
from .utils import send_call, send_applier
from chat.utils import send_super_message, create_room, send_notice_to_room

import pytz
from django.utils import timezone
from datetime import timedelta
from celery import shared_task
from django.db.models import Q

@shared_task
def call_control():
    for order_item in Order.objects.filter(Q(status = 0) | Q(status = 1)):
        # if collect ended at 
        if order_item.collect_ended_at < timezone.now():
            persons = order_item.person
            print("person is {}".format(persons))
            if order_item.status == 0 and order_item.joins.count() < persons:
                print("no casts applied")

                message = "誠に申し訳ございません。\n \
                    {}名のキャストをお探ししましたが募集人数に達しなかったためご予約をキャンセルさせていただきました。\n \
                    またのご利用心よりお待ちしております。\n \
                    \n \
                    応募キャスト : {}".format(persons, order_item.joins.count())
                order_item.status = 8
                order_item.save()

                # remove the order from application list of cast page
                user_ids = list(Member.objects.filter(location = order_item.parent_location, role = 0).values_list('id', flat = True))
                send_call(order_item, user_ids, "delete")

                # send super message to guest
                send_super_message("system", order_item.user.id, message)

                # send super message to applied casts
                cast_ids = list(order_item.joins.values_list('user_id', flat = True))
                for cast_id in cast_ids:
                    send_super_message("system", cast_id, message)

                send_call(order_item, cast_ids, "mine")
                
            if order_item.status == 1 and order_item.joins.filter(status = 1).count() < persons:
                
                # if remaining casts are less than required
                if order_item.joins.filter(status = 0, dropped = False).count() < persons - order_item.joins.filter(status = 1).count():
                    continue

                # order remaining casts by call times
                candidates = list(order_item.joins.filter(status = 0, dropped = False).order_by('user__call_times').values_list('id', flat = True))
                added_cast_ids = []
                for _ in range(persons - order_item.joins.filter(status = 1).count()):
                    candidate_id = candidates.pop(0)
                    added_cast_ids.append(candidate_id)
                    cur_join = Join.objects.get(pk = candidate_id)
                    cur_join.status = 1
                    cur_join.selection = 0
                    cur_join.save()
                
                # send cast ids call
                send_call(order_item, added_cast_ids, "create")

                # remove other joins
                remove_cast_ids = list(order_item.joins.filter(status = 0).values_list('user_id', flat = True))
                start_time_str = order_item.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
                message = "オーダーにエントリー頂き、誠にありが \
                    とうございました。 残念ながら「合流: {0} {1} キャスト{2}人」のマッチングでは外れました。\
                    是非またオーダーにエントリー頂けますようお願いいたします!".format(
                        order_item.location.name if order_item.location else order_item.location_other, start_time_str, order_item.person)
                for cast_id in remove_cast_ids:
                    send_super_message("system", cast_id, message)

                order_item.joins.filter(status = 0).delete()

                # make room for confirmed join casts
                room_id = create_room(order_item, list(order_item.joins.values_list('user_id', flat = True)))

                # notify guest
                send_applier(order_item.id, room_id, order_item.user_id)
        
@shared_task
def call_notify():
    for order_item in Order.objects.filter(status = 4):

        if order_item.room != None:
            
            # loop through join
            for join in order_item.joins.filter(is_started = True, is_ended = False):
                
                ended_predict = join.started_at + timedelta(hours = order_item.period)
                ten_ended_predict = ended_predict - timedelta(minutes = 10)
                cur_time = timezone.now()

                if not join.is_ten_left:

                    # check 10 minutes left
                    if ten_ended_predict < cur_time:
                        # update join
                        join.is_ten_left = True
                        join.save()

                        # notification
                        message = "終了予定10分前です。時間を過ぎると自動延長になります。"
                        order_item.room.last_message = message
                        order_item.room.save()
                        send_notice_to_room(order_item.room, message, True, join.user_id)
                else:

                    # check time extended
                    if ended_predict < cur_time:
                        # update join's extended state
                        join.is_extended = True
                        join.save()
                