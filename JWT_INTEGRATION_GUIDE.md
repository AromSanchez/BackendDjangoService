# Guía de Integración JWT - Spring Boot a Django

Esta guía explica cómo configurar Django para interpretar y validar JWT tokens generados por tu backend de Spring Boot.

## 📋 Configuración de Spring Boot

Tu backend de Spring Boot genera JWT tokens con:
- **Algoritmo**: HS256 (HMAC-SHA256)
- **Secret Key**: `mi_clave_super_secreta_para_jwt_1234567890`
- **Refresh Secret Key**: `mi_clave_diferente_para_refresh_token_0987654321`
- **Subject (sub)**: ID del usuario (Long convertido a String)
- **Expiración Access Token**: 30 minutos
- **Expiración Refresh Token**: 10 días

## 🚀 Pasos de Instalación

### 1. Instalar dependencias

```bash
pip install PyJWT==2.8.0
```

O usar el archivo actualizado:
```bash
pip install -r requirements_updated.txt
```

### 2. Configurar `settings.py`

Agrega las siguientes configuraciones a tu archivo `conectaya/settings.py`:

```python
# ============================================
# JWT CONFIGURATION
# ============================================
JWT_SECRET_KEY = "mi_clave_super_secreta_para_jwt_1234567890"
JWT_REFRESH_SECRET_KEY = "mi_clave_diferente_para_refresh_token_0987654321"

# ============================================
# MIDDLEWARE
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'conectaya.authentication.middleware.JWTAuthenticationMiddleware',  # ← AGREGAR AQUÍ
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# AUTHENTICATION BACKENDS
# ============================================
AUTHENTICATION_BACKENDS = [
    'conectaya.authentication.backends.JWTAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ============================================
# REST FRAMEWORK (Opcional)
# ============================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
}
```

### 3. Configurar URLs principales

Edita `conectaya/urls.py` para incluir las rutas de autenticación:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('conectaya.authentication.urls')),  # ← AGREGAR AQUÍ
]
```

## 📝 Uso

### Opción 1: Usar el Middleware (Automático)

El middleware `JWTAuthenticationMiddleware` intercepta automáticamente todas las requests y valida el token. No necesitas hacer nada adicional.

```python
# En cualquier vista
def mi_vista(request):
    if hasattr(request, 'jwt_user_id'):
        user_id = request.jwt_user_id
        return JsonResponse({'message': f'Usuario autenticado con ID: {user_id}'})
    else:
        return JsonResponse({'error': 'No autenticado'}, status=401)
```

### Opción 2: Usar Decoradores (Recomendado)

#### Para vistas Django estándar:

```python
from conectaya.authentication.decorators import jwt_required

@jwt_required
def mi_vista_protegida(request):
    user_id = request.jwt_user_id
    return JsonResponse({'message': f'Usuario ID: {user_id}'})
```

#### Para vistas Django REST Framework:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from conectaya.authentication.decorators import jwt_required_drf

@api_view(['GET'])
@jwt_required_drf
def mi_vista_protegida(request):
    user_id = request.jwt_user_id
    return Response({'message': f'Usuario ID: {user_id}'})
```

### Opción 3: Validación Manual

```python
from conectaya.authentication.jwt_utils import JWTUtils

def mi_vista(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user_id = JWTUtils.get_user_id_from_token(token)
        
        if user_id:
            return JsonResponse({'user_id': user_id, 'authenticated': True})
    
    return JsonResponse({'error': 'No autenticado'}, status=401)
```

## 🧪 Probar la Integración

### 1. Obtener un token desde Spring Boot

```bash
POST http://localhost:8080/api/auth/login
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "password123"
}
```

Respuesta:
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Usar el token en Django

```bash
GET http://localhost:8000/api/protected-drf/
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

Respuesta:
```json
{
  "message": "Usuario autenticado con ID: 1",
  "user_id": 1,
  "authenticated": true,
  "framework": "Django REST Framework"
}
```

## 📚 Endpoints de Ejemplo Disponibles

| Endpoint | Método | Autenticación | Descripción |
|----------|--------|---------------|-------------|
| `/api/public/` | GET | No | Vista pública sin autenticación |
| `/api/protected/` | GET | Sí | Vista protegida Django estándar |
| `/api/protected-drf/` | GET | Sí | Vista protegida DRF |
| `/api/user-info/` | GET | Sí | Información del usuario autenticado |

## 🔒 Seguridad

### ⚠️ IMPORTANTE: Cambiar las Secret Keys en Producción

Las secret keys actuales están hardcodeadas. Para producción:

1. **Usar variables de entorno**:

```python
# settings.py
import os

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default_key')
JWT_REFRESH_SECRET_KEY = os.environ.get('JWT_REFRESH_SECRET_KEY', 'default_refresh_key')
```

2. **Crear archivo `.env`**:

```env
JWT_SECRET_KEY=mi_clave_super_secreta_para_jwt_1234567890
JWT_REFRESH_SECRET_KEY=mi_clave_diferente_para_refresh_token_0987654321
```

3. **Instalar python-decouple**:

```bash
pip install python-decouple
```

```python
# settings.py
from decouple import config

JWT_SECRET_KEY = config('JWT_SECRET_KEY')
JWT_REFRESH_SECRET_KEY = config('JWT_REFRESH_SECRET_KEY')
```

## 🔧 Personalización

### Sincronizar usuarios entre Spring Boot y Django

Si quieres que Django cree automáticamente usuarios cuando se autentican con JWT:

```python
# En backends.py, el método authenticate busca por ID:
user = User.objects.filter(id=user_id).first()

# IMPORTANTE: Los usuarios deben existir en ambas bases de datos
# con el mismo ID. Django no crea usuarios automáticamente.
```

### Agregar claims personalizados

Si Spring Boot agrega más información al JWT (roles, permisos, etc.), puedes accederlos:

```python
from conectaya.authentication.jwt_utils import JWTUtils

payload = JWTUtils.decode_access_token(token)
user_id = int(payload.get('sub'))  # El ID viene como string
roles = payload.get('roles', [])  # Si Spring Boot agrega roles en el futuro
```

## 🐛 Troubleshooting

### Error: "Token inválido"
- Verifica que la secret key en Django sea exactamente la misma que en Spring Boot
- Verifica que el token no haya expirado (30 minutos)

### Error: "Token expirado"
- Usa el refresh token para obtener un nuevo access token desde Spring Boot

### Error: "No module named 'jwt'"
- Instala PyJWT: `pip install PyJWT==2.8.0`

## 📞 Soporte

Si tienes problemas, verifica:
1. Las secret keys son idénticas en ambos backends
2. El formato del header es: `Authorization: Bearer <token>`
3. El token no ha expirado
4. PyJWT está instalado correctamente
