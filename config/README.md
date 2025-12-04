# 🔥 INSTRUCCIONES: Configuración de Firebase

## Paso 1: Colocar la Clave Privada de Firebase

Debes colocar tu archivo de clave privada de Firebase (Service Account JSON) en esta ubicación:

```
BackendDjangoService/config/firebase-service-account.json
```

## Paso 2: Verificar el Nombre del Archivo

El archivo DEBE llamarse exactamente: **`firebase-service-account.json`**

## Paso 3: Seguridad

⚠️ **IMPORTANTE**: Este archivo contiene credenciales sensibles.

- ✅ Ya está agregado al `.gitignore`
- ❌ **NUNCA** lo subas a repositorios públicos
- ❌ **NUNCA** lo compartas públicamente

## Estructura Esperada del Archivo

Tu archivo `firebase-service-account.json` debe tener una estructura similar a esta:

```json
{
  "type": "service_account",
  "project_id": "tu-proyecto-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@tu-proyecto.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

## Verificación

Una vez colocado el archivo, el sistema de notificaciones push estará listo para funcionar.

Para verificar que todo funciona correctamente:

1. Inicia la app Android
2. Verifica en los logs que el token FCM se obtuvo correctamente
3. Crea una reserva y verifica que el proveedor reciba la notificación push
