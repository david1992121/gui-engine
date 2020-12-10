from __future__ import absolute_import, unicode_literals
from .models import Member
from celery import shared_task
from django.utils import timezone

@shared_task
def present_cast():
    for user in Member.objects.filter(is_present = True, role = 0):
        if user.presented_at < timezone.now():
            user.is_present = False
            user.presented_at = None
            user.save()
