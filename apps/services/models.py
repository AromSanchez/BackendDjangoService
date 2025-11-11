"""
Modelos de servicios
"""
from django.db import models
from django.utils.text import slugify
from apps.users.models import User


class Category(models.Model):
    """
    Categorías de servicios
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # emoji o nombre
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # Para ordenar en el front
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(models.Model):
    """
    Servicios ofrecidos por proveedores
    """
    provider_id = models.BigIntegerField(db_index=True)  # FK a users
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='services')
    
    # Información básica
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Ubicación
    location_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Estados
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Campos calculados (para optimizar queries)
    reviews_count = models.IntegerField(default=0)
    rating_sum = models.IntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    favorites_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    bookings_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'services'
        indexes = [
            models.Index(fields=['provider_id']),
            models.Index(fields=['category', 'is_published', 'is_active']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['-rating_avg']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def provider(self):
        """Helper para obtener el proveedor"""
        try:
            return User.objects.get(id=self.provider_id)
        except User.DoesNotExist:
            return None


class ServiceImage(models.Model):
    """
    Imágenes de un servicio
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    file_id = models.BigIntegerField()  # FK a files de Spring Boot
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_images'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['service', 'order']),
        ]
