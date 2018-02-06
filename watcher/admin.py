from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Website, TelegramUser

class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('url', 'user_id', 'last_seen','last_status')
admin.site.register(Website, WebsiteAdmin)


class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id',)
admin.site.register(TelegramUser, TelegramUserAdmin)
