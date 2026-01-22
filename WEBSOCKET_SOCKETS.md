# WebSockets de Habitto

## Introducción

Este documento reúne todos los sockets disponibles en la aplicación, sus rutas y los eventos que emiten. Está pensado para que el frontend pueda suscribirse y reaccionar (por ejemplo, mostrar animaciones de match).

## Autenticación

- Los sockets de notificaciones validan que el `user_id` de la URL coincida con el usuario autenticado.
- La autenticación depende del middleware de Channels configurado en el proyecto (sesión/JWT).

## Endpoints de WebSocket

### Chat en tiempo real

- **URL**: `ws://<host>/ws/chat/<room_id>/`
- **room_id**: `<min(sender_id)>-<max(receiver_id)>`

### Inbox de conversaciones

- **URL**: `ws://<host>/ws/chat/inbox/<user_id>/`
- **Uso**: notifica nuevos mensajes para refrescar la lista de conversaciones.

### Notificaciones (alias de inbox)

- **URL**: `ws://<host>/ws/notifications/<user_id>/`
- **Uso**: misma estructura de payload que el inbox.

### Notificaciones de propiedades

- **URL**: `ws://<host>/ws/property-notifications/<user_id>/`
- **Uso**: likes y matches relacionados con propiedades del propietario o agente.

### Notificaciones de inquilino

- **URL**: `ws://<host>/ws/tenant-notifications/<user_id>/`
- **Uso**: eventos de match aceptado por propietario/agente para el inquilino.

## Eventos y payloads

### Chat

**Evento recibido en sala de chat**:

```json
{
  "id": 123,
  "room_id": "5-7",
  "roomId": "5-7",
  "sender": 5,
  "receiver": 7,
  "content": "Hola!",
  "created_at": "2025-11-14T12:34:56Z",
  "createdAt": "2025-11-14T12:34:56Z",
  "is_read": false
}
```

**Evento recibido en inbox/notifications**:

```json
{
  "message_id": 123,
  "sender": 5,
  "receiver": 7,
  "content": "Hola!",
  "created_at": "2025-11-14T12:34:56Z",
  "counterpart_full_name": "Juan Pérez",
  "counterpart_profile_picture": "https://..."
}
```

### Notificaciones de propiedades

**Like a propiedad**:

```json
{
  "type": "property_like",
  "property_id": 45,
  "property_title": "departamento en Calle Falsa 123",
  "interested_user": {
    "id": 5,
    "username": "juan",
    "full_name": "Juan Pérez",
    "profile_picture": "https://..."
  },
  "timestamp": "2025-11-14T12:34:56Z",
  "notification_id": "uuid"
}
```

Campos adicionales posibles en `interested_user`: `email`, `first_name`, `last_name`, `phone`, `user_type` (según disponibilidad).

**Match aceptado (notificación al propietario/agente)**:

```json
{
  "type": "match_accepted",
  "property_id": 45,
  "property_title": "departamento en Calle Falsa 123",
  "property_address": "Calle Falsa 123",
  "owner_contact": { "email": "owner@mail.com", "phone": "+591..." },
  "match_status": "accepted",
  "next_steps": [
    "Contactar al inquilino para coordinar visita",
    "Verificar documentación",
    "Coordinar firma de contrato"
  ],
  "timestamp": "2025-11-14T12:34:56Z",
  "notification_id": "uuid"
}
```

### Notificaciones de inquilino

**Match aceptado por propietario/agente**:

```json
{
  "type": "match_accepted_by_owner",
  "property_id": 45,
  "property_title": "departamento en Calle Falsa 123",
  "property_address": "Calle Falsa 123",
  "owner_name": "Juan Pérez",
  "owner_contact": { "email": "owner@mail.com", "phone": "+591..." },
  "match_score": 87.5,
  "next_steps": [
    "Contactar al propietario para coordinar visita",
    "Preparar documentación necesaria",
    "Coordinar fecha de mudanza"
  ],
  "timestamp": "2025-11-14T12:34:56Z",
  "notification_id": "uuid"
}
```

## Flujo de match con socket (animación de match)

1. El inquilino da like a una propiedad (`POST /api/matches/{id}/like/` o `POST /api/properties/{id}/like/`).
2. El propietario/agente acepta el match (`POST /api/matches/{id}/owner_accept/`).
3. Se emite `match_accepted_by_owner` al canal del inquilino:
   - **Socket**: `ws://<host>/ws/tenant-notifications/<tenant_user_id>/`
   - **Acción en frontend**: disparar animación de match.

## Ping/Pong

Los sockets de notificaciones aceptan:

```json
{ "type": "ping" }
```

Respuesta:

```json
{ "type": "pong", "timestamp": "2025-11-14T12:34:56Z" }
```
