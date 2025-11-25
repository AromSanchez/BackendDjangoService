# 🚀 Desplegar Django Backend en Render - Guía Rápida

## ✅ Pre-requisitos Completados

- ✅ PostgreSQL configurado en el código
- ✅ Credenciales de Render ya incluidas
- ✅ Gunicorn agregado a requirements.txt
- ✅ Todo listo para desplegar

---

## 📋 Paso 1: Crear Web Service en Render

1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Clic en **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub/GitLab
4. Selecciona el repositorio del backend Django

---

## ⚙️ Paso 2: Configuración del Servicio

### Información Básica

| Campo | Valor |
|-------|-------|
| **Name** | `conectaya-django-backend` |
| **Region** | Selecciona la misma región que tu base de datos |
| **Branch** | `main` (o tu rama principal) |
| **Root Directory** | `BackendDjangoService` (si está en subdirectorio) |
| **Environment** | `Python 3` |

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python manage.py migrate && gunicorn conectaya.wsgi:application --bind 0.0.0.0:$PORT
```

### Plan
- Selecciona **Free** (para pruebas) o **Starter** ($7/mes)

---

## 🎯 Paso 3: Desplegar

1. Haz clic en **"Create Web Service"**
2. Render comenzará a construir tu aplicación
3. Espera a que el estado cambie a **"Live"** (5-10 minutos)

**¡Eso es todo!** No necesitas configurar variables de entorno, todo está en el código.

---

## ✅ Paso 4: Verificar

### Tu aplicación estará en:
```
https://conectaya-django-backend.onrender.com
```

### Probar endpoints:
```bash
# API
curl https://conectaya-django-backend.onrender.com/api/

# Admin
https://conectaya-django-backend.onrender.com/admin/
```

---

## 🔧 Crear Superusuario (Opcional)

1. En Render Dashboard, ve a tu Web Service
2. Clic en **"Shell"** en el menú superior
3. Ejecuta:
```bash
python manage.py createsuperuser
```

---

## 🔄 Auto-Deploy

Cada vez que hagas `git push`, Render desplegará automáticamente.

```bash
git add .
git commit -m "Update backend"
git push origin main
```

---

## 🐛 Si algo falla

### Ver logs:
- En Render Dashboard → Tu servicio → Pestaña **"Logs"**

### Problemas comunes:

**Error: "Application failed to respond"**
- Verifica que el Start Command sea correcto
- Verifica que gunicorn esté en requirements.txt

**Error: "Database connection failed"**
- Verifica que la base de datos PostgreSQL esté activa en Render
- Verifica que esté en la misma región

---

## 📊 Archivos Configurados

- ✅ `settings.py` - PostgreSQL configurado
- ✅ `requirements.txt` - psycopg2-binary y gunicorn agregados
- ✅ Todo listo para producción

---

## 🎉 ¡Listo!

Tu backend Django está configurado y listo. Solo necesitas:

1. **Crear Web Service en Render**
2. **Configurar Build y Start Commands**
3. **Desplegar**

¡Eso es todo! 🚀
