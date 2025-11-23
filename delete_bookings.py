from apps.bookings.models import Booking

# Contar bookings antes de eliminar
count = Booking.objects.all().count()
print(f"📊 Total de bookings encontrados: {count}")

# Eliminar todos los bookings
if count > 0:
    Booking.objects.all().delete()
    print(f"✅ Eliminados {count} bookings exitosamente")
else:
    print("ℹ️ No hay bookings para eliminar")
