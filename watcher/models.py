from django.db import models
from django.conf import settings
from django.utils import timezone
import requests

# Create your models here.
class Website(models.Model):
    telegram_user = models.ForeignKey("TelegramUser",on_delete=models.CASCADE)
    user_id = models.CharField('Telegram user id',max_length=30)
    last_seen = models.DateTimeField('last time seen ok',null=True)
    last_checked = models.DateTimeField('last time checked',null=True)
    last_status = models.IntegerField('last status checked',null=True)
    last_reason = models.CharField('last reason checked',max_length=30, null=True)
    wrong_count = models.IntegerField('count wrong checked',default=0)
    url = models.CharField('URL', max_length=75)
    active = models.IntegerField(default=1)

    def __unicode__( self ):
        return self.url

    def save_status_code(self):
        code, reason = self._get_status_code(self.url)
        self.last_checked = timezone.now()
        self.last_status = code
        self.last_reason = reason
        if not code in (200, 401):
            self.wrong_count += 1
        else:
            self.last_seen = timezone.now()
            self.wrong_count = 0
        self.save()
        return code

    def _get_status_code(self, url):
        """ This function retreives the status code of a website by requesting
            HEAD data from the host. This means that it only requests the headers.
            If the host cannot be reached or something else goes wrong, it returns
            None instead. 
        """
        try:
            r = requests.head(url)
            return (r.status_code, r.reason)
        except requests.ConnectionError:
            return (-1,'Error')

class TelegramUser(models.Model):
    user_id = models.CharField('Telegram user id',max_length=30)
    chat_id = models.CharField('Telegram chat id',max_length=30)
    chat_disabled = models.IntegerField('if chat is disabled',default=1)
    pro =  models.IntegerField('if pro then 100 sites',default=0)
    def __unicode__( self ):
        return self.user_id
    