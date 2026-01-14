# Documentación de la API de Habitto

Esta documentación detalla los endpoints disponibles en la API REST de Habitto.

## Índice

1. [Autenticación y Sesiones](#1-autenticación-y-sesiones)
2. [Gestión de Usuarios y Perfiles](#2-gestión-de-usuarios-y-perfiles)
3. [Propiedades y Unidades](#3-propiedades-y-unidades)
4. [Matching y Roommates](#4-matching-y-roommates)
5. [Comunicación (Mensajes y Notificaciones)](#5-comunicación)
6. [Finanzas (Pagos e Incentivos)](#6-finanzas)
7. [Sistema y Utilidades (Uploads, Reportes)](#7-sistema-y-utilidades)
8. [Mapas y Zonas](#8-mapas-y-zonas)

---

## 1. Autenticación y Sesiones

### Autenticación JWT

El sistema utiliza **Access Token** (60 min) y **Refresh Token** (7 días).
Todas las peticiones protegidas requieren el header:
`Authorization: Bearer <access_token>`

#### Endpoints

| Método | Endpoint                  | Descripción                               |
| ------ | ------------------------- | ----------------------------------------- |
| `POST` | `/api/login/`             | Iniciar sesión (Username/Password)        |
| `POST` | `/api/refresh/`           | Renovar Access Token usando Refresh Token |
| `POST` | `/dj-rest-auth/google/`   | Login Social con Google (Token Implícito) |
| `POST` | `/dj-rest-auth/facebook/` | Login Social con Facebook                 |
| `POST` | `/dj-rest-auth/apple/`    | Login Social con Apple                    |

#### Login con Google (Móvil)

Enviar el `access_token` obtenido del SDK de Google en el dispositivo.

```json
POST /dj-rest-auth/google/
{
  "access_token": "ya29.a0AfB_byD..."
}
```

---

## 2. Gestión de Usuarios y Perfiles

### Usuarios

| Método | Endpoint         | Descripción             |
| ------ | ---------------- | ----------------------- |
| `POST` | `/api/users/`    | Registrar nuevo usuario |
| `GET`  | `/api/users/me/` | Obtener usuario actual  |

**Registro (Payload):**

```json
{
  "username": "juanperez",
  "email": "juan@example.com",
  "password": "securePass123",
  "first_name": "Juan",
  "last_name": "Perez"
}
```

### Perfiles

El perfil se crea automáticamente al registrar el usuario.
| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/profiles/me/` | Ver mi perfil extendido |
| `PATCH` | `/api/profiles/update_me/` | Actualizar mi perfil |

**Actualización de Perfil (Ejemplo):**

```json
{
  "bio": "Estudiante de arquitectura, busco lugar tranquilo.",
  "phone_number": "+59170000000",
  "birth_date": "1995-05-20",
  "gender": "male"
}
```

---

## 3. Propiedades y Unidades

### Propiedades (CRUD)

| Método   | Endpoint                | Descripción                              |
| -------- | ----------------------- | ---------------------------------------- |
| `GET`    | `/api/properties/`      | Listar propiedades (Filtros disponibles) |
| `POST`   | `/api/properties/`      | Crear propiedad                          |
| `GET`    | `/api/properties/{id}/` | Ver detalle (incluye unidades)           |
| `PATCH`  | `/api/properties/{id}/` | Editar propiedad                         |
| `DELETE` | `/api/properties/{id}/` | Eliminar propiedad                       |

**Crear Propiedad (Payload Completo):**

```json
{
  "type": "departamento", // casa, departamento, habitacion, anticretico
  "address": "Av. Banzer 4to Anillo",
  "latitude": -17.7834, // Requerido si no es Unidad
  "longitude": -63.1821, // Requerido si no es Unidad
  "price": 450.0,
  "guarantee": 450.0, // Opcional
  "description": "Hermoso depto...",
  "bedrooms": 2,
  "bathrooms": 1,
  "size": 80.5, // m2
  "amenities": ["WiFi", "Piscina", "Garaje"], // Puede ser lista de IDs o Nombres
  "photos_urls": [
    "https://res.cloudinary.com/...",
    "https://res.cloudinary.com/..."
  ],
  "pets_allowed": true,
  "allows_roommates": true
}
```

### Unidades (Sub-propiedades)

Para crear un departamento dentro de un edificio ya registrado.

1.  **Crear:** Usar `POST /api/properties/` enviando `parent_property_id`.
2.  **Ubicación:** No enviar `latitude`/`longitude`, se hereda del padre.
3.  **Listar:** Al hacer GET al padre, las unidades vienen en el campo `units`.

**Crear Unidad (Ejemplo):**

```json
{
  "type": "departamento",
  "address": "Av. Banzer (Misma del padre)",
  "price": 500.0,
  "parent_property_id": 15, // ID del Edificio
  "unit_number": "2B",
  "bedrooms": 2
}
```

### Fotos y Amenidades

| Método   | Endpoint            | Descripción                             |
| -------- | ------------------- | --------------------------------------- |
| `GET`    | `/api/amenities/`   | Listar todas las amenidades disponibles |
| `POST`   | `/api/photos/`      | Subir foto asociada a una propiedad     |
| `DELETE` | `/api/photos/{id}/` | Eliminar una foto específica            |

---

## 4. Matching y Roommates

### Perfil de Búsqueda (SearchProfile)

Define qué busca el usuario (zona, precio, compañeros).
| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/search_profiles/me/` | Obtener mi perfil de búsqueda |
| `POST` | `/api/search_profiles/` | Crear/Actualizar perfil de búsqueda |

**Payload SearchProfile:**

```json
{
  "budget_min": 200,
  "budget_max": 500,
  "latitude": -17.78, // Centro de búsqueda
  "longitude": -63.18,
  "radius": 5, // km
  "roommate_preference": "looking", // none, open, looking
  "vibes": ["Estudioso", "Fiesta", "Fitness"],
  "amenities": ["WiFi"]
}
```

### Matches y Feedback

El sistema genera matches automáticamente. El usuario da feedback (Like/Dislike).
| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/matches/` | Ver mis matches pendientes |
| `POST` | `/api/match_feedback/` | Dar Like/Dislike/Superlike |

**Dar Feedback (Swipe):**

```json
POST /api/match_feedback/
{
  "match_id": 1024,
  "feedback_type": "like" // like, dislike, superlike
}
```

---

## 5. Comunicación

### Mensajería

| Método | Endpoint              | Descripción               |
| ------ | --------------------- | ------------------------- |
| `GET`  | `/api/messages/`      | Listar mis conversaciones |
| `POST` | `/api/messages/`      | Enviar mensaje            |
| `GET`  | `/api/messages/{id}/` | Ver hilo de conversación  |

**Enviar Mensaje:**

```json
{
  "receiver": 45, // ID del usuario destino
  "content": "Hola, sigue disponible?",
  "property": 12 // Opcional, si es sobre una propiedad
}
```

### Notificaciones

| Método  | Endpoint                   | Descripción                         |
| ------- | -------------------------- | ----------------------------------- |
| `GET`   | `/api/notifications/`      | Listar mis notificaciones           |
| `PATCH` | `/api/notifications/{id}/` | Marcar como leída (`is_read: true`) |

---

## 6. Finanzas

### Pagos

| Método | Endpoint         | Descripción        |
| ------ | ---------------- | ------------------ |
| `GET`  | `/api/payments/` | Historial de pagos |
| `POST` | `/api/payments/` | Registrar un pago  |

### Métodos de Pago

| Método | Endpoint                | Descripción               |
| ------ | ----------------------- | ------------------------- |
| `GET`  | `/api/payment-methods/` | Métodos de pago guardados |

### Incentivos

| Método | Endpoint           | Descripción                         |
| ------ | ------------------ | ----------------------------------- |
| `GET`  | `/api/incentives/` | Ver incentivos disponibles en zonas |

---

## 7. Sistema y Utilidades

### Subida de Imágenes

| Método | Endpoint             | Descripción               |
| ------ | -------------------- | ------------------------- |
| `POST` | `/api/upload/image/` | Subir imagen a Cloudinary |

**Headers:** `Content-Type: multipart/form-data`
**Body:** `file` (Binary), `folder` (Texto, opcional)
**Respuesta:**

```json
{
  "url": "https://res.cloudinary.com/.../image.jpg",
  "filename": "image.jpg"
}
```

### Reportes

| Método | Endpoint        | Descripción                  |
| ------ | --------------- | ---------------------------- |
| `POST` | `/api/reports/` | Reportar usuario o propiedad |

**Payload Reporte:**

```json
{
  "target_type": "property", // user, property
  "target_property": 15, // ID si es propiedad
  "title": "Estafa",
  "description": "Pide dinero adelantado sin mostrar...",
  "severity": "high"
}
```

---

## 8. Mapas y Zonas

### Zonas Inteligentes

Para visualización de mapas de calor y zonas hexagonales.
Ver documentación detallada en: [zones.md](./zones.md)

| Método | Endpoint               | Descripción                         |
| ------ | ---------------------- | ----------------------------------- |
| `GET`  | `/api/map/zones/`      | GeoJSON de zonas hexagonales        |
| `GET`  | `/api/properties/map/` | GeoJSON de propiedades individuales |
