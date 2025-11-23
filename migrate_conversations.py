from apps.chat.models import Conversation

# Actualizar conversaciones que tienen booking pero no tienen service_id
conversations = Conversation.objects.filter(booking__isnull=False, service_id__isnull=True)
count = 0

for conv in conversations:
    if conv.booking and conv.booking.service:
        conv.service_id = conv.booking.service.id
        conv.save()
        count += 1
        print(f"✅ Conversación {conv.id} actualizada con service_id={conv.service_id}")

print(f"\n📊 Total de conversaciones actualizadas: {count}")
