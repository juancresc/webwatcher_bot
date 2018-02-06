from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('webhook/522306030:AAEOJUQwL0N9EXJFRYPN9AoRcmxlr7rmHBg/', views.webhook, name='webhook'),
]