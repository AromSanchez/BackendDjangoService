"""
Views para el módulo de servicios
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
from .models import Service, Category
from .serializers import ServiceSerializer, CategorySerializer


@api_view(['GET', 'POST'])
@jwt_required_drf
def services_list_create(request):
    """
    GET: Lista servicios del proveedor autenticado
    POST: Crea un nuevo servicio
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Obtener servicios del proveedor
            services = Service.objects.filter(provider_id=user_id).order_by('-created_at')
            serializer = ServiceSerializer(services, many=True)
            return Response({
                'services': serializer.data,
                'count': services.count()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Verificar que el usuario sea proveedor
            if user.role != 'PROVIDER':
                return Response(
                    {'error': 'Solo los proveedores pueden crear servicios'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Crear servicio
            data = request.data.copy()
            data['provider_id'] = user_id
            
            serializer = ServiceSerializer(data=data)
            if serializer.is_valid():
                service = serializer.save()
                return Response(
                    ServiceSerializer(service).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT', 'DELETE'])
@jwt_required_drf
def service_detail(request, service_id):
    """
    GET: Obtiene detalles de un servicio
    PUT: Actualiza un servicio
    DELETE: Elimina un servicio
    """
    try:
        user_id = request.jwt_user_id
        service = get_object_or_404(Service, id=service_id)
        
        # Verificar permisos (solo el proveedor puede modificar/eliminar)
        if request.method in ['PUT', 'DELETE'] and service.provider_id != user_id:
            return Response(
                {'error': 'No tienes permisos para modificar este servicio'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            serializer = ServiceSerializer(service)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = ServiceSerializer(service, data=request.data, partial=True)
            if serializer.is_valid():
                service = serializer.save()
                return Response(
                    ServiceSerializer(service).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            service.delete()
            return Response(
                {'message': 'Servicio eliminado correctamente'},
                status=status.HTTP_204_NO_CONTENT
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def services_public_list(request):
    """
    Lista pública de servicios (para clientes)
    """
    try:
        # Filtros
        category = request.GET.get('category')
        search = request.GET.get('search')
        location = request.GET.get('location')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        
        # Query base
        services = Service.objects.filter(is_published=True, is_active=True)
        
        # Aplicar filtros
        if category:
            services = services.filter(category__slug=category)
        
        if search:
            services = services.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        if location:
            services = services.filter(location_type__icontains=location)
        
        if min_price:
            services = services.filter(price__gte=min_price)
        
        if max_price:
            services = services.filter(price__lte=max_price)
        
        # Ordenar por rating y fecha
        services = services.order_by('-rating_avg', '-created_at')
        
        serializer = ServiceSerializer(services, many=True)
        return Response({
            'services': serializer.data,
            'count': services.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def categories_list(request):
    """
    Lista todas las categorías activas
    """
    try:
        categories = Category.objects.filter(is_active=True).order_by('order', 'name')
        serializer = CategorySerializer(categories, many=True)
        return Response({
            'categories': serializer.data,
            'count': categories.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
