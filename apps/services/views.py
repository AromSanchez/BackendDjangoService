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
            # Admin puede ver todos los servicios, proveedores solo los suyos
            if user.role == 'ADMIN':
                services = Service.objects.all()
            else:
                services = Service.objects.filter(provider_id=user_id)

            # Filtros opcionales
            category = request.GET.get('category')
            status_filter = request.GET.get('status')
            search = request.GET.get('search')

            if category:
                services = services.filter(category__slug__iexact=category)

            if status_filter:
                if status_filter.lower() == 'active':
                    services = services.filter(is_active=True, is_published=True)
                elif status_filter.lower() == 'pending':
                    services = services.filter(is_published=False)
                elif status_filter.lower() == 'inactive':
                    services = services.filter(is_active=False)

            if search:
                services = services.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(provider__full_name__icontains=search)
                )

            services = services.order_by('-created_at')
            
            # Paginación
            page = int(request.GET.get('page', 1))
            page_size = 9
            total_count = services.count()
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            
            # Calcular índices de paginación
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            # Obtener servicios de la página actual
            paginated_services = services[start_index:end_index]
            
            serializer = ServiceSerializer(paginated_services, many=True)
            return Response({
                'services': serializer.data,
                'count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Verificar que el usuario sea proveedor o admin
            if user.role not in ['PROVIDER', 'ADMIN']:
                return Response(
                    {'error': 'Solo los proveedores y administradores pueden crear servicios'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Crear servicio
            data = request.data.copy()
            data['provider_id'] = user_id
            
            # Debug: Imprimir datos recibidos
            print(f"📝 Datos recibidos para crear servicio: {data}")
            print(f"👤 Usuario: {user.full_name} (ID: {user_id}, Rol: {user.role})")
            
            serializer = ServiceSerializer(data=data)
            if serializer.is_valid():
                service = serializer.save()
                print(f"✅ Servicio creado exitosamente: {service.id}")
                return Response(
                    ServiceSerializer(service).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                return Response({
                    'error': 'Datos inválidos',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
        user = get_object_or_404(User, id=user_id)
        service = get_object_or_404(Service, id=service_id)
        
        # Verificar permisos (proveedor dueño o administrador)
        if request.method in ['PUT', 'DELETE']:
            if service.provider_id != user_id and user.role != 'ADMIN':
                return Response(
                    {'error': 'No tienes permisos para modificar este servicio'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        if request.method == 'GET':
            serializer = ServiceSerializer(service, context={'request': request})
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
        
        # Paginación
        page = int(request.GET.get('page', 1))
        page_size = 9
        total_count = services.count()
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        
        # Calcular índices de paginación
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Obtener servicios de la página actual
        paginated_services = services[start_index:end_index]
        
        # Use ServiceListSerializer with context for is_favorite
        from .serializers import ServiceListSerializer
        serializer = ServiceListSerializer(paginated_services, many=True, context={'request': request})
        
        response_data = {
            'services': serializer.data,
            'count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
        
        # Debug log
        print(f"📊 Pagination Response: total={total_count}, pages={total_pages}, current={page}, services_returned={len(serializer.data)}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
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


# ============= ADMIN CATEGORY MANAGEMENT =============

@api_view(['GET', 'POST'])
@jwt_required_drf
def admin_categories_list_create(request):
    """
    GET: Lista todas las categorías (admin)
    POST: Crea una nueva categoría (admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea admin
        if user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para gestionar categorías'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            # Filtros
            search = request.GET.get('search', '')
            status_filter = request.GET.get('status', '')
            
            categories = Category.objects.all()
            
            if search:
                categories = categories.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if status_filter:
                if status_filter.lower() == 'active':
                    categories = categories.filter(is_active=True)
                elif status_filter.lower() == 'inactive':
                    categories = categories.filter(is_active=False)
            
            categories = categories.order_by('order', 'name')
            
            # Paginación
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 15))
            total_count = categories.count()
            total_pages = (total_count + page_size - 1) // page_size
            
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_categories = categories[start_index:end_index]
            
            serializer = CategorySerializer(paginated_categories, many=True)
            return Response({
                'results': serializer.data,
                'count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            from .serializers import CategoryCreateUpdateSerializer
            serializer = CategoryCreateUpdateSerializer(data=request.data)
            if serializer.is_valid():
                category = serializer.save()
                return Response(
                    CategorySerializer(category).data,
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
def admin_category_detail(request, category_id):
    """
    GET: Obtiene detalles de una categoría
    PUT: Actualiza una categoría
    DELETE: Elimina una categoría
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea admin
        if user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para gestionar categorías'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        category = get_object_or_404(Category, id=category_id)
        
        if request.method == 'GET':
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            from .serializers import CategoryCreateUpdateSerializer
            serializer = CategoryCreateUpdateSerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                category = serializer.save()
                return Response(
                    CategorySerializer(category).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Verificar si tiene servicios asociados
            services_count = category.services.count()
            if services_count > 0:
                return Response(
                    {'error': f'No se puede eliminar la categoría porque tiene {services_count} servicio(s) asociado(s)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            category.delete()
            return Response(
                {'message': 'Categoría eliminada correctamente'},
                status=status.HTTP_204_NO_CONTENT
            )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@jwt_required_drf
def admin_category_toggle_status(request, category_id):
    """
    Activa o desactiva una categoría
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea admin
        if user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para gestionar categorías'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        category = get_object_or_404(Category, id=category_id)
        category.is_active = not category.is_active
        category.save()
        
        return Response(
            CategorySerializer(category).data,
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ============= ADMIN CATEGORY MANAGEMENT =============

@api_view(['GET', 'POST'])
@jwt_required_drf
def admin_categories_list_create(request):
    """
    GET: Lista todas las categorías (admin)
    POST: Crea una nueva categoría (admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea admin
        if user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para gestionar categorías'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            # Filtros
            search = request.GET.get('search', '')
            status_filter = request.GET.get('status', '')
            
            categories = Category.objects.all()
            
            if search:
                categories = categories.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if status_filter:
                if status_filter.lower() == 'active':
                    categories = categories.filter(is_active=True)
                elif status_filter.lower() == 'inactive':
                    categories = categories.filter(is_active=False)
            
            categories = categories.order_by('order', 'name')
            
            # Paginación
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 15))
            total_count = categories.count()
            total_pages = (total_count + page_size - 1) // page_size
            
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_categories = categories[start_index:end_index]
            
            serializer = CategorySerializer(paginated_categories, many=True)
            return Response({
                'results': serializer.data,
                'count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            from .serializers import CategoryCreateUpdateSerializer
            serializer = CategoryCreateUpdateSerializer(data=request.data)
            if serializer.is_valid():
                category = serializer.save()
                return Response(
                    CategorySerializer(category).data,
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
def admin_category_detail(request, category_id):
    """
    GET: Obtiene detalles de una categoría
    PUT: Actualiza una categoría
    DELETE: Elimina una categoría
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea admin
        if user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para gestionar categorías'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        category = get_object_or_404(Category, id=category_id)
        
        if request.method == 'GET':
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            from .serializers import CategoryCreateUpdateSerializer
            serializer = CategoryCreateUpdateSerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                category = serializer.save()
                return Response(
                    CategorySerializer(category).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Verificar si tiene servicios asociados
            services_count = category.services.count()
            if services_count > 0:
                return Response(
                    {'error': f'No se puede eliminar la categoría porque tiene {services_count} servicio(s) asociado(s)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            category.delete()
            return Response(
                {'message': 'Categoría eliminada correctamente'},
                status=status.HTTP_204_NO_CONTENT
            )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@jwt_required_drf
def admin_category_toggle_status(request, category_id):
    """
    Activa o desactiva una categoría
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea admin
        if user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para gestionar categorías'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        category = get_object_or_404(Category, id=category_id)
        category.is_active = not category.is_active
        category.save()
        
        return Response(
            CategorySerializer(category).data,
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

