"""
Modelos para el módulo Dashboard
Mapea la tabla 'users' existente de Spring Boot sin crear migraciones
"""
from django.db import models


class User(models.Model):
    """
    Modelo User que mapea a la tabla 'users' existente en MySQL
    
    IMPORTANTE: Este modelo NO debe generar migraciones.
    Usa la tabla creada por Spring Boot.
    """
    
    # Choices para el campo role
    CUSTOMER = 'CUSTOMER'
    PROVIDER = 'PROVIDER'
    ADMIN = 'ADMIN'
    
    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (PROVIDER, 'Provider'),
        (ADMIN, 'Admin'),
    ]
    
    # Choices para provider_status
    NONE = 'NONE'
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    
    PROVIDER_STATUS_CHOICES = [
        (NONE, 'None'),
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    # Campos del modelo (mapean a la tabla users)
    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(
        max_length=12,
        choices=ROLE_CHOICES,
        default=CUSTOMER
    )
    is_active = models.BooleanField(default=True)
    provider_status = models.CharField(
        max_length=20,
        choices=PROVIDER_STATUS_CHOICES,
        default=NONE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'  # Usa la tabla existente
        managed = False  # Django NO gestiona esta tabla (no crea migraciones)
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def is_customer(self):
        """Verifica si el usuario es cliente"""
        return self.role == self.CUSTOMER
    
    @property
    def is_provider(self):
        """Verifica si el usuario es proveedor"""
        return self.role == self.PROVIDER
    
    @property
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == self.ADMIN
    
    def get_role_display_name(self):
        """Retorna el nombre legible del rol"""
        return dict(self.ROLE_CHOICES).get(self.role, 'Unknown')
