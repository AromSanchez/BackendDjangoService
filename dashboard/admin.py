"""
Admin configuration para el módulo Dashboard
"""
from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo User
    """
    list_display = ['id', 'full_name', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'provider_status']
    search_fields = ['full_name', 'email', 'phone_number']
    readonly_fields = ['id', 'created_at', 'password']  # Password readonly por seguridad
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('id', 'full_name', 'email', 'phone_number', 'phone_verified_at')
        }),
        ('Autenticación', {
            'fields': ('password',),
            'description': 'El password está hasheado y no se puede ver en texto plano.'
        }),
        ('Roles y Permisos', {
            'fields': ('role', 'is_active', 'provider_status')
        }),
        ('Fechas', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Deshabilitar creación desde Django admin (se crea desde Spring Boot)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Deshabilitar eliminación desde Django admin (se gestiona desde Spring Boot)"""
        return False
