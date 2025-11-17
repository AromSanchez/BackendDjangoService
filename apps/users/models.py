"""
Modelos de usuarios
"""
from django.db import models


class User(models.Model):
    """
    Modelo de solo lectura para acceder a usuarios de Spring Boot
    NO gestiona la tabla, solo la lee
    """
    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=20)  # CUSTOMER, PROVIDER, ADMIN
    is_active = models.BooleanField(default=True)
    onboarding_status = models.CharField(max_length=20, default='PENDING')
    pending_role_choice = models.CharField(max_length=20, null=True, blank=True)
    auth_provider = models.CharField(max_length=20, default='LOCAL')
    provider_status = models.CharField(max_length=20)  # NONE, PENDING, APPROVED, REJECTED
    created_at = models.DateTimeField()
    
    class Meta:
        managed = False  # Django NO gestiona esta tabla
        db_table = 'users'
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def is_customer(self):
        """Verifica si el usuario es cliente"""
        return self.role == 'CUSTOMER'
    
    @property
    def is_provider(self):
        """Verifica si el usuario es proveedor"""
        return self.role == 'PROVIDER'
    
    @property
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == 'ADMIN'


class UserProfile(models.Model):
    """
    Perfil extendido del usuario (datos adicionales del marketplace)
    """
    user_id = models.BigIntegerField(unique=True, db_index=True)  # FK a Spring Boot
    bio = models.TextField(blank=True, null=True, max_length=500)
    avatar_file_id = models.BigIntegerField(null=True, blank=True)  # FK a files
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Perú')
    
    # Configuraciones de usuario
    notification_email = models.BooleanField(default=True)
    notification_push = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['city']),
        ]
    
    def __str__(self):
        return f"Profile of user {self.user_id}"
    
    @property
    def user(self):
        """Helper para obtener el usuario de Spring Boot"""
        try:
            return User.objects.get(id=self.user_id)
        except User.DoesNotExist:
            return None
