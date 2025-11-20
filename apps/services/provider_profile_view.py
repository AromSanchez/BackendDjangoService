"""
Vista para obtener el perfil público de un proveedor
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Avg

from apps.users.models import User, UserProfile
from apps.services.models import Service
from apps.bookings.models import Booking


@api_view(['GET'])
def provider_public_profile(request, provider_id):
    """
    Obtiene el perfil público completo de un proveedor
    Incluye: información del usuario, perfil, servicios, estadísticas
    """
    try:
        # Obtener proveedor
        provider = get_object_or_404(User, id=provider_id, role='PROVIDER', is_active=True)
        
        # Obtener perfil
        try:
            profile = UserProfile.objects.get(user_id=provider_id)
            profile_image = profile.avatar_file_id if hasattr(profile, 'avatar_file_id') else None
            banner_image = profile.banner_file_id if hasattr(profile, 'banner_file_id') else None
            bio = profile.bio or ""
        except UserProfile.DoesNotExist:
            profile_image = None
            banner_image = None
            bio = ""
        
        # Obtener servicios del proveedor
        services = Service.objects.filter(
            provider_id=provider_id,
            is_published=True,
            is_active=True
        ).order_by('-created_at')
        
        # Calcular estadísticas
        total_services = services.count()
        
        # Rating promedio del proveedor (promedio de todos sus servicios)
        avg_rating = services.aggregate(Avg('rating_avg'))['rating_avg__avg'] or 0
        
        # Servicios completados
        completed_services = Booking.objects.filter(
            provider_id=provider_id,
            status='COMPLETED'
        ).count()
        
        # Serializar servicios
        from apps.services.serializers import ServiceListSerializer
        services_data = ServiceListSerializer(services, many=True, context={'request': request}).data
        
        # Construir respuesta
        response_data = {
            'user': {
                'id': provider.id,
                'full_name': provider.full_name,
                'email': provider.email,
                'role': provider.role,
                'created_at': provider.created_at
            },
            'profile_image': profile_image,
            'banner_image': banner_image,
            'bio': bio,
            'average_rating': round(avg_rating, 1) if avg_rating else 0,
            'total_services': total_services,
            'completed_services': completed_services,
            'services': services_data,
            'achievements': []  # Placeholder para futuros logros
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error en provider_public_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
