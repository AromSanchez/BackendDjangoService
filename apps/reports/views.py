"""
Views para el módulo de reports
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
from .models import Report
from .serializers import (
    ReportSerializer, ReportListSerializer, ReportCreateSerializer,
    ReportModerationSerializer
)


@api_view(['GET', 'POST'])
@jwt_required_drf
def reports_list_create(request):
    """
    GET: Lista reportes del usuario autenticado
    POST: Crea un nuevo reporte
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Lista reportes del usuario
            reports = Report.objects.filter(reporter_id=user_id).order_by('-created_at')
            
            # Filtros opcionales
            status_filter = request.GET.get('status')
            if status_filter:
                reports = reports.filter(status=status_filter)
            
            serializer = ReportListSerializer(reports, many=True)
            return Response({
                'reports': serializer.data,
                'count': reports.count()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Crear reporte
            data = request.data.copy()
            serializer = ReportCreateSerializer(
                data=data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                # No se puede reportar a sí mismo
                reported_user_id = serializer.validated_data.get('reported_user_id')
                if reported_user_id == user_id:
                    return Response(
                        {'error': 'No puedes reportarte a ti mismo'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                report = serializer.save(reporter_id=user_id)
                
                return Response(
                    ReportSerializer(report).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def report_detail(request, report_id):
    """
    Obtiene detalles de un reporte
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        report = get_object_or_404(Report, id=report_id)
        
        # Solo el reporter o admin pueden ver el reporte
        if report.reporter_id != user_id and user.role != 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para ver este reporte'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ADMIN ENDPOINTS

@api_view(['GET'])
@jwt_required_drf
def admin_reports_list(request):
    """
    Lista todos los reportes para moderación (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filtros
        status_filter = request.GET.get('status', 'open')
        reason_filter = request.GET.get('reason')
        
        reports = Report.objects.all()
        
        if status_filter:
            reports = reports.filter(status=status_filter)
        
        if reason_filter:
            reports = reports.filter(reason=reason_filter)
        
        reports = reports.order_by('-created_at')
        
        serializer = ReportModerationSerializer(reports, many=True)
        return Response({
            'reports': serializer.data,
            'count': reports.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@jwt_required_drf
def admin_report_update(request, report_id):
    """
    Actualizar estado de un reporte (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report = get_object_or_404(Report, id=report_id)
        
        serializer = ReportModerationSerializer(
            report,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            report = serializer.save()
            return Response(
                ReportModerationSerializer(report).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def admin_report_resolve(request, report_id):
    """
    Resolver un reporte (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report = get_object_or_404(Report, id=report_id)
        
        if report.status in ['resolved', 'dismissed']:
            return Response(
                {'error': 'El reporte ya está resuelto'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action', 'resolved')  # resolved, dismissed
        admin_notes = request.data.get('admin_notes', '')
        
        if action not in ['resolved', 'dismissed']:
            return Response(
                {'error': 'Acción inválida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.status = action
        report.admin_notes = admin_notes
        report.admin_user_id = user_id
        report.resolved_at = timezone.now()
        report.save()
        
        return Response(
            ReportModerationSerializer(report).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def admin_reports_stats(request):
    """
    Estadísticas de reportes (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count
        
        # Estadísticas generales
        total_reports = Report.objects.count()
        open_reports = Report.objects.filter(status='open').count()
        in_review_reports = Report.objects.filter(status='in_review').count()
        resolved_reports = Report.objects.filter(status='resolved').count()
        dismissed_reports = Report.objects.filter(status='dismissed').count()
        
        # Estadísticas por razón
        reason_stats = Report.objects.values('reason').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Reportes recientes
        recent_reports = Report.objects.filter(
            status='open'
        ).order_by('-created_at')[:10]
        
        recent_serializer = ReportModerationSerializer(recent_reports, many=True)
        
        return Response({
            'total_reports': total_reports,
            'open_reports': open_reports,
            'in_review_reports': in_review_reports,
            'resolved_reports': resolved_reports,
            'dismissed_reports': dismissed_reports,
            'reason_stats': list(reason_stats),
            'recent_reports': recent_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
