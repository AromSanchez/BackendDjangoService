# Estructura Correcta de Settings en Django

## ✅ Configuración Correcta

Django debe tener **UN SOLO archivo `settings.py`** en producción.

### Estructura actual (CORRECTA):
```
BackendDjangoService/
├── conectaya/
│   ├── __init__.py
│   ├── settings.py          ← ✅ ÚNICO archivo de configuración
│   ├── urls.py
│   ├── wsgi.py
│   └── authentication/      ← Módulo de autenticación JWT
│       ├── __init__.py
│       ├── jwt_utils.py
│       ├── middleware.py
│       ├── backends.py
│       ├── decorators.py
│       ├── views.py
│       └── urls.py
└── manage.py
```

## ❌ Lo que NO debes hacer

**NO tener múltiples archivos de settings**:
```
❌ settings.py
❌ settings_jwt.py
❌ settings_UPDATED.py
❌ settings_dev.py
❌ settings_prod.py
```

## 📋 Configuraciones JWT en settings.py

Tu `settings.py` ahora incluye:

### 1. JWT Secret Keys
```python
JWT_SECRET_KEY = "mi_clave_super_secreta_para_jwt_1234567890"
JWT_REFRESH_SECRET_KEY = "mi_clave_diferente_para_refresh_token_0987654321"
```

### 2. JWT Middleware
```python
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'conectaya.authentication.middleware.JWTAuthenticationMiddleware',  # ← JWT
    ...
]
```

### 3. Authentication Backends
```python
AUTHENTICATION_BACKENDS = [
    'conectaya.authentication.backends.JWTAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 4. REST Framework
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
}
```

## 🔧 Configuración Avanzada (Opcional)

Si en el futuro necesitas diferentes configuraciones para desarrollo y producción, usa **variables de entorno**:

### Opción 1: python-decouple
```bash
pip install python-decouple
```

```python
# settings.py
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
JWT_SECRET_KEY = config('JWT_SECRET_KEY')
```

```env
# .env
DEBUG=True
JWT_SECRET_KEY=mi_clave_super_secreta_para_jwt_1234567890
```

### Opción 2: django-environ
```bash
pip install django-environ
```

```python
# settings.py
import environ

env = environ.Env()
environ.Env.read_env()

DEBUG = env.bool('DEBUG', default=False)
JWT_SECRET_KEY = env('JWT_SECRET_KEY')
```

## 🚀 Buenas Prácticas

### ✅ Hacer:
- Usar UN SOLO `settings.py`
- Usar variables de entorno para valores sensibles
- Documentar las configuraciones personalizadas
- Mantener las secret keys fuera del código (usar `.env`)

### ❌ No hacer:
- Crear múltiples archivos de settings
- Hardcodear secret keys en producción
- Commitear archivos `.env` al repositorio
- Duplicar configuraciones

## 📁 Archivos de Configuración Permitidos

Los únicos archivos de configuración que deberías tener:

```
conectaya/
├── settings.py          ← Configuración principal
├── urls.py              ← URLs principales
├── wsgi.py              ← WSGI config
└── asgi.py              ← ASGI config (opcional)
```

## 🔐 Seguridad

### En Desarrollo:
```python
# settings.py
DEBUG = True
JWT_SECRET_KEY = "mi_clave_super_secreta_para_jwt_1234567890"
```

### En Producción:
```python
# settings.py
import os
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
JWT_SECRET_KEY = config('JWT_SECRET_KEY')
SECRET_KEY = config('SECRET_KEY')

# .env (NO commitear)
DEBUG=False
JWT_SECRET_KEY=clave_super_segura_aleatoria_en_produccion
SECRET_KEY=otra_clave_django_segura
```

## 📝 Resumen

1. ✅ **Ahora tienes UN SOLO `settings.py`** con todas las configuraciones JWT
2. ✅ **Eliminados archivos de referencia** (`settings_jwt.py`, `settings_UPDATED.py`)
3. ✅ **Configuración lista para usar**
4. 🔜 **Próximo paso**: Usar variables de entorno en producción

## 🎯 Estado Actual

Tu proyecto está configurado correctamente con:
- ✅ Un solo `settings.py`
- ✅ JWT configurado
- ✅ Middleware activado
- ✅ Authentication backends configurados
- ✅ REST Framework configurado

**¡Listo para usar!** 🚀
