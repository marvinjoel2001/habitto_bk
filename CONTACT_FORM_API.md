# Endpoint de Contacto (Formulario Web)

## Resumen

Este endpoint recibe la información de un formulario de contacto y envía un correo al destinatario configurado en el backend.

## Endpoint

`POST /api/contact/`

## Autenticación

No requerida.

## Request (JSON)

Campos obligatorios:

- `full_name`: nombre completo
- `email`: correo del remitente
- `subject`: asunto
- `message`: mensaje

Campos opcionales:

- `logo_url`: URL del logo a mostrar en la plantilla
- `content_image_url`: URL de imagen principal en la plantilla

### Ejemplo

```json
{
  "full_name": "Marvin Joel Peña",
  "email": "marvinjoelpena@gmail.com",
  "subject": "Consulta sobre Habitto",
  "message": "Hola, quiero más información.",
  "logo_url": "https://tuservidor.com/logo.png",
  "content_image_url": "https://tuservidor.com/contenido.png"
}
```

## Response (201/200)

```json
{
  "success": true,
  "message": "Mensaje enviado exitosamente",
  "data": {
    "status": "sent",
    "to": "marvinjoelpena@gmail.com"
  }
}
```

## Errores comunes

- `400 Bad Request`: campos obligatorios faltantes o email inválido
- `500 Internal Server Error`: configuración de email incompleta

## Configuración necesaria

Variables de entorno:

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`
- `CONTACT_RECIPIENT_EMAIL`

## Carpeta de imágenes para la plantilla

Ubicación: `email_assets/contact/`

Nombres sugeridos para los archivos:

- `logo.png`
- `contenido.png`
