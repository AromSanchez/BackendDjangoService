"""
URLs para el módulo de chat
"""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # CRUD básico de conversaciones
    path('conversations/', views.conversations_list_create, name='conversations_list_create'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Mensajes
    path('conversations/<int:conversation_id>/messages/', views.conversation_messages, name='conversation_messages'),
    path('conversations/<int:conversation_id>/read/', views.conversation_mark_read, name='conversation_mark_read'),
    
    # Mensajes avanzados
    path('conversations/<int:conversation_id>/booking-action/', views.send_booking_action_message, name='send_booking_action_message'),
    path('conversations/<int:conversation_id>/file/', views.send_file_message, name='send_file_message'),
    path('conversations/<int:conversation_id>/search/', views.conversation_search_messages, name='conversation_search_messages'),
    
    # Utilidades
    path('booking/<int:booking_id>/', views.conversation_by_booking, name='conversation_by_booking'),
    path('stats/', views.chat_stats, name='chat_stats'),
    path('unread/', views.conversations_unread_count, name='conversations_unread_count'),
]
