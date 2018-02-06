from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import watcher.telegram as telegram
import json
from django.conf import settings

bot = telegram.Bot(settings.TELEGRAM_TOKEN)

def index(request):
    context = {'latest_question_list': "das"}
    return render(request, 'watcher/index.html', context)

@csrf_exempt
def webhook(request):
    return bot.parse_request(request)