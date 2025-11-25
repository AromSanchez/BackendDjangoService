# ⚡ Comandos para Render - Copy & Paste

## 🎯 Configuración en Render Dashboard

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python manage.py migrate && gunicorn conectaya.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 🚀 Desplegar Cambios

```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

---

## 🔧 Crear Superusuario

En Render Shell:
```bash
python manage.py createsuperuser
```

---

## ✅ Verificar Deployment

```bash
curl https://tu-app.onrender.com/api/
```

---

## 📋 Configuración Render

- **Name:** `conectaya-django-backend`
- **Environment:** `Python 3`
- **Branch:** `main`
- **Auto-Deploy:** ✅ Yes

---

¡Eso es todo! No necesitas variables de entorno, todo está configurado en el código.
