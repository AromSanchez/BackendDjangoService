"""
URLs para el módulo de chat
"""
"""
URLs para el módulo de chat
"""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Conversaciones
    path('conversations/', views.conversations_list_create, name='conversations-list-create'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', views.conversation_messages, name='conversation-messages'),
    path('conversations/<int:conversation_id>/mark-read/', views.conversation_mark_read, name='conversation-mark-read'),
    path('conversations/<int:conversation_id>/clear-history/', views.clear_conversation_history, name='clear-conversation-history'),
    path('conversations/<int:conversation_id>/delete/', views.delete_conversation, name='delete-conversation'),
    path('conversations/<int:conversation_id>/create-booking/', views.create_booking_from_chat, name='create-booking-from-chat'),
    path('conversations/<int:conversation_id>/send-action/', views.send_booking_action_message, name='send-booking-action'),
    path('conversations/<int:conversation_id>/send-file/', views.send_file_message, name='send-file-message'),
    path('conversations/<int:conversation_id>/search/', views.conversation_search_messages, name='conversation-search'),
    
    # Obtener conversación por booking o servicio
    path('conversations/by-booking/<int:booking_id>/', views.conversation_by_booking, name='conversation-by-booking'),
    path('conversations/by-service/<int:service_id>/', views.create_or_get_conversation_by_service, name='conversation-by-service'),
    
    # Estadísticas
    path('stats/', views.chat_stats, name='chat-stats'),
    path('unread-count/', views.conversations_unread_count, name='unread-count'),
    
    # Ganancias del proveedor
    path('provider/earnings/', views.get_provider_earnings, name='provider-earnings'),
]
