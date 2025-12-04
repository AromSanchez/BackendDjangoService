# 🔥 Configuración de Firebase en Render

## Paso 1: Copiar el Contenido del Archivo JSON

Abre tu archivo `config/firebase-service-account.json` y copia TODO el contenido (debe ser un JSON completo).

## Paso 2: Crear Variable de Entorno en Render

1. Ve a tu servicio de Django en Render Dashboard
2. Ve a la sección **Environment**
3. Agrega una nueva variable de entorno:
   - **Key**: `FIREBASE_CREDENTIALS_JSON`
   - **Value**: Pega TODO el contenido del archivo JSON (debe empezar con `{` y terminar con `}`)

Ejemplo del valor:
```json
{"type":"service_account","project_id":"tu-proyecto","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

## Paso 3: Guardar y Redesplegar

1. Click en **Save Changes**
2. Render redesplegará automáticamente tu servicio
3. Las notificaciones push funcionarán correctamente

## ✅ Ventajas de este Método

- ✅ No necesitas subir credenciales a GitHub
- ✅ Más seguro
- ✅ Fácil de actualizar si cambias las credenciales
- ✅ El código detecta automáticamente si usar archivo local o variable de entorno

## 🔍 Verificación

En los logs de Render deberías ver:
```
🔥 Firebase inicializado desde variable de entorno
```

Si ves esto, significa que está funcionando correctamente.
