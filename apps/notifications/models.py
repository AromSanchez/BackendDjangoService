from django.db import models


class DeviceToken(models.Model):
    # Almacena el user_id de Spring Boot (no es una FK a Django)
    user_id = models.IntegerField(db_index=True)
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=50, default='ANDROID')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_tokens'
        indexes = [
            models.Index(fields=['user_id']),
        ]
    
    def __str__(self):
        return f"User {self.user_id} - {self.device_type}"
