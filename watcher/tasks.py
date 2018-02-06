# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.schedules import crontab
from celery import Celery
from watcher.models import Website
from watcher.telegram import Bot
from datetime import timedelta
from django.conf import settings
import math
from django.utils import timezone

@shared_task
def check_websites():
    websites = Website.objects.filter(active=1).filter(wrong_count=0).order_by('-last_checked')
    for website in websites:
        check_website(website)

@shared_task
def check_wrong_websites():
    #time_threshold = datetime.now() - timedelta(minutes=1)
    #.filter(last_checked__lt=time_threshold)
    websites = Website.objects.filter(active=1).filter(wrong_count__gte=1).order_by('-last_checked')
    for website in websites:
        minutes = math.pow(2,website.wrong_count)
        time_threshold = timezone.now() - timedelta(minutes=minutes)
        if website.last_checked < time_threshold:
            check_website(website)

def check_website(website):
    last_wrong = not website.last_status in (200, 401, None)
    code = website.save_status_code()
    bot = Bot(settings.TELEGRAM_TOKEN)
    if code in (200, 401):
        if last_wrong:
            text_params = (website.url, )
            params = {'text':'Website %s is back online!' % text_params }
            bot.send_message(website.telegram_user.chat_id,params)
        else:
            pass
    else:
        minutes = math.pow(2,website.wrong_count)
        if code == -1:
            text_params = (website.url, minutes, )
            params = {'text':'Website %s down! Site unreachable. Will check again in at least %i minutes' % text_params }
        else:
            text_params = (website.url, code, minutes,)
            params = {'text':'Website %s down! Response code %s. Will check again in at least %i minutes' % text_params }
        bot.send_message(website.telegram_user.chat_id,params)
