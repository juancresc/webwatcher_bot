import requests
import json
from django.http import HttpResponse
import shlex
import redis
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .models import Website, TelegramUser
import json
import timeago, datetime
from django.utils import timezone

class Bot():
    def __init__(self, token):
        self._token = token
        self._url = 'https://api.telegram.org/bot' + self._token + '/'
        self._redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.__DEFAULT = 'I can monitor your websites and notify you if any of them are down. Add up to 3 websites in starter. Start typing / for getting the list of commands'
        self.__HELP = 'To add a website send /add http://yourwebsite.com - Remember to add http:// or https:// accordingly.'

    def send_message(self, chat_id,  kwargs = {}):
        '''
        What the fox says
        '''
        params = {'chat_id': chat_id, 'disable_web_page_preview': 'true'}
        params = {**params, **kwargs}
        r = requests.get(self._url + 'sendMessage', params=params)
        return r

    def parse_request(self, request):
        body_unicode = request.body.decode('utf-8')
        try:
            body = json.loads(body_unicode)
        except ValueError:
            return HttpResponse("No valid json in payload")
        
        try:
            user_id = body['message']['from']['id']
            chat_id = body['message']['chat']['id']
            message_id = body['message']['message_id']
            username = body['message']['from']['username']
            text = body['message']['text']
        except KeyError:
            return HttpResponse("No valid keys in payload")
        telegram_user = self._get_user(user_id, chat_id)

        kwargs = {
            'user_id': str(user_id),
            'chat_id': str(chat_id),
            'message_id': message_id,
            'username': str(username),
            'text': str(text),
            'telegram_user': telegram_user,
        }

        if text[0] == "/":
            values = shlex.split(text)
            if values[0] == '/start':
                self.send_message(chat_id, self._start(user_id,username))
            if values[0] == '/list':
                self.send_message(chat_id, self._list(kwargs, values))
            if values[0] == '/help':
                self.send_message(chat_id, self._help(kwargs, values))
            if values[0] == '/remove':
                self.send_message(chat_id, self._remove(kwargs, values))
            if values[0] == '/add':
                self.send_message(chat_id, self._add(kwargs, values))
        else:
            #NOT a command
            values = shlex.split(text)
            self.send_message(chat_id, self._plain_parse(kwargs, values))
        return HttpResponse("OK")
    
    def _get_user(self, user_id, chat_id):
        telegram_user = TelegramUser.objects.filter(user_id=user_id).first()
        if not telegram_user: 
            telegram_user = TelegramUser()
            telegram_user.user_id = user_id
        telegram_user.chat_id = chat_id
        telegram_user.save()
        return telegram_user

    def _help(self, kwargs, values):
        return {'text': self.__HELP}

    def _list(self, kwargs, values):
        self._redis.set('state-' + kwargs['user_id'], 'list')
        websites = Website.objects.filter(active=1).filter(user_id=kwargs['user_id'])
        out_str = ''
        if not websites.exists():
            self._reset_states(kwargs['user_id'])
            return {'text':'There are not websites in you watchlist, start adding using /add'}
        for website in websites:
            if website.last_reason == None:
                last_reason = '?'
            else:
                last_reason = str(website.last_reason)
            if website.last_status == None:
                last_status = '?'
            else:
                last_status = str(website.last_status)
            
            #calculate time ago
            if website.last_checked != None:
                timeago_str = timeago.format(website.last_checked, timezone.now())
            else:
                timeago_str = '?'

            out_str += website.url
            out_str += '\n'
            out_str += '<b>Status</b>: ' + last_status + ' ' + last_reason 
            out_str += '\n'
            out_str += '(' +  timeago_str + ')'
            out_str += '\n'
            out_str += '\n'
        return {'text': out_str, 'parse_mode':'HTML'}

    def _start(self, user_id, username):
        return {'text':"Welcome %s!" % (username, )}

    def _remove(self, kwargs, values):
        if len(values) == 1:
            websites = Website.objects.filter(active=1).filter(user_id=kwargs['user_id'])
            keys = []
            if not websites.exists():
                self._reset_states(kwargs['user_id'])
                return {'text':'There are not websites in you watchlist, start adding using /add'}
            keyboard = []
            for website in websites:
                keys = []
                keys.append(website.url)
                keyboard.append(keys)
            self._redis.set('state-' + kwargs['user_id'], 'remove')
            self._redis.set('step-' + kwargs['user_id'], '1')
            self._redis.set('msgid-' + kwargs['user_id'], kwargs['message_id'])

            reply_markup =  { 'keyboard': keyboard, 'one_time_keyboard': True}
            reply_markup = json.dumps(reply_markup)
            return { 'text': 'Select the URL of the website you want me to remove from watchlist',
                    'reply_markup': reply_markup,
                    }
        if len(values) > 2:
            self._reset_states(kwargs['user_id'])
            return {'text':"Please send me only one URL at the time."}
        url = values[1]
        val = URLValidator()
        try:
            val(url)
        except ValidationError:
            self._reset_states(kwargs['user_id'])
            return {'text':"I've skiped %s since it is not a valid URL" % url}
        
        website = Website.objects.filter(active=1).filter(url=url).filter(user_id=kwargs['user_id'])
        if not website.exists():
            self._reset_states(kwargs['user_id'])
            return {'text':"I have not found %s in your watchlist" % (url, )}
        website.delete()
        self._reset_states(kwargs['user_id'])
        return {'text':"I have Removed %s from watchlist!" % (url, )}

    def _add(self, kwargs, values):
        websites = Website.objects.filter(active=1).filter(user_id=kwargs['user_id'])
        if kwargs['telegram_user'].pro == 1:
            max_sites = 100
        else:
            max_sites = 3
        if websites.count() >= max_sites:
            return {'text':"You cannot add more than %i sites" % (max_sites,)}
        if len(values) == 1:
            self._redis.set('state-' + kwargs['user_id'], 'add')
            self._redis.set('step-' + kwargs['user_id'], '1')
            self._redis.set('msgid-' + kwargs['user_id'], kwargs['message_id'])
            return {'text':"Send me the URL of the new website you want me to add to the watchlisht (Don't forget to add http(s)://"}
        if len(values) > 2:
            self._reset_states(kwargs['user_id'])
            return {'text':"Please send only one URL at the time"}
        url = values[1]
        val = URLValidator()
        try:
            val(url)
        except ValidationError:
            self._reset_states(kwargs['user_id'])
            return {'text':"I've skiped %s since it is not a valid URL" % url}
        
        exists = Website.objects.filter(active=1).filter(url=url).exists()
        if exists:
            self._reset_states(kwargs['user_id'])
            return {'text':"URL %s already exists in your watchlist" % (url, )}
        website = Website()
        website.url = url
        website.telegram_user = kwargs['telegram_user']
        website.user_id = kwargs['user_id']
        website.save()
        self._reset_states(kwargs['user_id'])
        return {'text':"Added %s to the watchlist!" % (url, )}
        #validate url
        

    def _plain_parse(self, kwargs, values):
        text = kwargs['text']
        #ADD
        if self._redis.get('state-' + str(kwargs['user_id'])) == b'add':
            #STEP 1
            if self._redis.get('step-' + str(kwargs['user_id'])) == b'1':
                # CORRECT MSG ID
                if str(kwargs['message_id'] - 2) == str(self._redis.get('msgid-' + kwargs['user_id']),'utf-8'):
                    val = URLValidator()
                    try:
                        val(text)
                    except ValidationError:
                        self._reset_states(kwargs['user_id'])
                        return {'text':"I've skiped %s since it is not a valid URL" % text}
                    exists = Website.objects.filter(active=1).filter(url=text).exists()
                    if exists:
                        self._reset_states(kwargs['user_id'])
                        return {'text':"URL %s already exists in your watchlist" % (text, )}
                    website = Website()
                    website.url = text
                    website.telegram_user = kwargs['telegram_user']
                    website.user_id = kwargs['user_id']
                    website.save()
                    self._reset_states(kwargs['user_id'])
                    return {'text':"Website added"}
        #REMOVE
        if self._redis.get('state-' + str(kwargs['user_id'])) == b'remove':
            #STEP 1
            if self._redis.get('step-' + str(kwargs['user_id'])) == b'1':
                # CORRECT MSG ID
                if str(kwargs['message_id'] - 2) == str(self._redis.get('msgid-' + kwargs['user_id']),'utf-8'):
                    val = URLValidator()
                    try:
                        val(text)
                    except ValidationError:
                        return {'text':"I've skiped %s since it is not a valid URL" % text}
                    website = Website.objects.filter(active=1).filter(url=text).filter(user_id=kwargs['user_id'])
                    if not website.exists():
                        self._reset_states(kwargs['user_id'])
                        return {'text':"I have not found %s in your watchlist" % (text, )}
                    website.delete()
                    self._reset_states(kwargs['user_id'])
                    return {'text':"I have removed %s from watchlist!" % (text, )}
#        self._reset_states(kwargs['user_id'])
        return {'text':self.__DEFAULT}

    def _reset_states(self, user_id):
        self._redis.set('state-' + user_id, 'idle')
        self._redis.set('msgid-' + user_id, '-1')
        self._redis.set('step-' + user_id, '0')