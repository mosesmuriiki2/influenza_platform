from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='messages_inbox'),
    path('sent/', views.sent_messages, name='messages_sent'),
    path('view/<int:message_id>/', views.view_message, name='view_message'),
    path('compose/', views.compose, name='compose_message'),
    path('reply/<int:message_id>/', views.reply, name='reply_message'),
]