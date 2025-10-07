# Documentación de la API de Habitto

Este documento describe los endpoints de la API del proyecto Habitto.

## Autenticación

La mayoría de los endpoints requieren autenticación por token. Para autenticarte, debes incluir el token en la cabecera `Authorization` de tus peticiones:

`Authorization: Token <tu_token>`

## 1. Endpoints de Usuarios (`/api/users/`)

Gestiona los usuarios del sistema.

### `POST /api/users/`

- **Descripción**: Registra un nuevo usuario.
- **Autenticación**: No requerida.
- **Request Body**:
  ```json
  {
    "username": "nuevo_usuario",
    "email": "usuario@example.com",
    "password": "tu_password_segura",
    "first_name": "Nombre",
    "last_name": "Apellido"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "username": "nuevo_usuario",
    "email": "usuario@example.com",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "date_joined": "2023-10-27T10:00:00Z"
  }
  ```

### `GET /api/users/`

- **Descripción**: Obtiene una lista de todos los usuarios.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "username": "usuario1",
      "email": "usuario1@example.com",
      "first_name": "Nombre1",
      "last_name": "Apellido1",
      "date_joined": "2023-10-27T10:00:00Z"
    },
    {
      "id": 2,
      "username": "usuario2",
      "email": "usuario2@example.com",
      "first_name": "Nombre2",
      "last_name": "Apellido2",
      "date_joined": "2023-10-27T11:00:00Z"
    }
  ]
  ```

## 2. Endpoints de Perfiles de Usuario (`/api/profiles/`)

Gestiona los perfiles asociados a los usuarios.

### `POST /api/profiles/`

- **Descripción**: Crea un perfil para el usuario autenticado.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "user_type": "inquilino", // o 'propietario', 'agente'
    "phone": "+1234567890",
    "favorites": [1, 2] // IDs de propiedades favoritas
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "user": {
      "id": 1,
      "username": "usuario1",
      "email": "usuario1@example.com"
    },
    "user_type": "inquilino",
    "phone": "+1234567890",
    "is_verified": false,
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T10:00:00Z",
    "favorites": [1, 2]
  }
  ```

### `POST /api/profiles/{id}/verify/`

- **Descripción**: Marca un perfil de usuario como verificado.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "status": "verified"
  }
  ```

## 3. Endpoints de Propiedades (`/api/properties/`)

Gestiona las propiedades inmobiliarias del sistema.

### `GET /api/properties/`

- **Descripción**: Obtiene una lista de propiedades con opciones de filtrado, búsqueda y ordenamiento.
- **Autenticación**: No requerida.
- **Parámetros de consulta**:
  - `type`: Filtra por tipo de propiedad (casa, departamento, habitación, anticretico)
  - `is_active`: Filtra por estado de la propiedad (true/false)
  - `owner`: Filtra por ID del propietario
  - `search`: Búsqueda en dirección y descripción
  - `ordering`: Ordena por `price` o `created_at` (prefija con `-` para orden descendente)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "type": "casa",
      "address": "Calle Falsa 123",
      "price": 1500.00,
      "guarantee": 1500.00,
      "description": "Casa amplia en zona residencial",
      "bedrooms": 3,
      "bathrooms": 2,
      "size": 120.5,
      "is_active": true,
      "created_at": "2023-10-07T10:00:00Z",
      "updated_at": "2023-10-07T10:00:00Z",
      "owner": 1,
      "agent": null,
      "amenities": [1, 2, 3],
      "accepted_payment_methods": [1, 2]
    }
  ]
  ```

### `POST /api/properties/`

- **Descripción**: Crea una nueva propiedad.
- **Autenticación**: Requerida (usuario debe ser propietario o agente).
- **Request Body**:
  ```json
  {
    "type": "casa",
    "address": "Calle Falsa 123",
    "latitude": -16.5000,
    "longitude": -68.1500,
    "price": 1500.00,
    "guarantee": 1500.00,
    "description": "Casa amplia en zona residencial",
    "size": 120.5,
    "bedrooms": 3,
    "bathrooms": 2,
    "amenities": [1, 2, 3],
    "availability_date": "2023-11-01",
    "accepted_payment_methods": [1, 2]
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "type": "casa",
    "address": "Calle Falsa 123",
    "price": 1500.00,
    "guarantee": 1500.00,
    "description": "Casa amplia en zona residencial",
    "bedrooms": 3,
    "bathrooms": 2,
    "size": 120.5,
    "is_active": true,
    "created_at": "2023-10-07T10:00:00Z",
    "updated_at": "2023-10-07T10:00:00Z",
    "owner": 1,
    "agent": null,
    "amenities": [1, 2, 3],
    "accepted_payment_methods": [1, 2]
  }
  ```

### `GET /api/properties/{id}/`

- **Descripción**: Obtiene los detalles de una propiedad específica.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "type": "casa",
    "address": "Calle Falsa 123",
    "price": 1500.00,
    "guarantee": 1500.00,
    "description": "Casa amplia en zona residencial",
    "bedrooms": 3,
    "bathrooms": 2,
    "size": 120.5,
    "is_active": true,
    "created_at": "2023-10-07T10:00:00Z",
    "updated_at": "2023-10-07T10:00:00Z",
    "owner": 1,
    "agent": null,
    "amenities": [1, 2, 3],
    "accepted_payment_methods": [1, 2]
  }
  ```

### `PUT /api/properties/{id}/`

- **Descripción**: Actualiza una propiedad existente.
- **Autenticación**: Requerida (solo propietario o agente asignado).
- **Request Body**: Igual que en POST, pero con campos opcionales.
- **Response (200 OK)**: Devuelve la propiedad actualizada.

### `DELETE /api/properties/{id}/`

- **Descripción**: Elimina una propiedad.
- **Autenticación**: Requerida (solo propietario o administrador).
- **Response (204 No Content)**: Sin contenido en la respuesta.

## 4. Endpoints de Fotos (`/api/photos/`)

Gestiona las fotos de las propiedades.

### `GET /api/photos/`

- **Descripción**: Obtiene una lista de todas las fotos de propiedades.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "property": 1,
      "image": "https://ejemplo.com/media/properties/1/foto1.jpg",
      "caption": "Fachada de la propiedad",
      "created_at": "2023-10-07T10:00:00Z"
    },
    {
      "id": 2,
      "property": 1,
      "image": "https://ejemplo.com/media/properties/1/foto2.jpg",
      "caption": "Sala de estar",
      "created_at": "2023-10-07T11:00:00Z"
    }
  ]
  ```

### `POST /api/photos/`

- **Descripción**: Sube una nueva foto para una propiedad.
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Request Body (multipart/form-data)**:
  - `property` (obligatorio): ID de la propiedad a la que pertenece la foto
  - `image` (obligatorio): Archivo de imagen
  - `caption` (opcional): Descripción de la foto
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "image": "https://ejemplo.com/media/properties/1/foto1.jpg",
    "caption": "Fachada de la propiedad",
    "created_at": "2023-10-07T10:00:00Z"
  }
  ```

### `GET /api/photos/{id}/`

- **Descripción**: Obtiene los detalles de una foto específica.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "image": "https://ejemplo.com/media/properties/1/foto1.jpg",
    "caption": "Fachada de la propiedad",
    "created_at": "2023-10-07T10:00:00Z"
  }
  ```

### `PUT /api/photos/{id}/`

- **Descripción**: Actualiza la descripción de una foto.
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Request Body**:
  ```json
  {
    "caption": "Nueva descripción de la foto"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "image": "https://ejemplo.com/media/properties/1/foto1.jpg",
    "caption": "Nueva descripción de la foto",
    "created_at": "2023-10-07T10:00:00Z"
  }
  ```

### `DELETE /api/photos/{id}/`

- **Descripción**: Elimina una foto.
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Response (204 No Content)**: Sin contenido en la respuesta.

## 5. Endpoints de Amenidades (`/api/amenities/`)

Gestiona las amenidades disponibles para las propiedades.

Nota: el modelo de `Amenity` en el proyecto solo contiene el campo `name`.

### `GET /api/amenities/`

- **Descripción**: Obtiene una lista de todas las amenidades disponibles.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "name": "Piscina"
    },
    {
      "id": 2,
      "name": "Gimnasio"
    }
  ]
  ```

### `POST /api/amenities/`

- **Descripción**: Crea una nueva amenidad.
- **Autenticación**: Requerida (normalmente por usuarios autenticados; los permisos concretos dependen del ViewSet).
- **Request Body**:
  ```json
  {
    "name": "Sauna"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 3,
    "name": "Sauna"
  }
  ```

## 6. Endpoints de Garantías (`/api/guarantees/`)

Gestiona las garantías de las propiedades.

El modelo de `Guarantee` contiene: `property`, `tenant`, `amount`, `is_released`, `release_date`, `created_at`.

### `GET /api/guarantees/`

- **Descripción**: Obtiene una lista de todas las garantías.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "property": 1,
      "tenant": 2,
      "amount": 1500.00,
      "is_released": false,
      "release_date": null,
      "created_at": "2023-10-07T10:00:00Z"
    }
  ]
  ```

### `POST /api/guarantees/`

- **Descripción**: Crea una nueva garantía.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "property": 1,
    "tenant": 2,
    "amount": 1500.00
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "tenant": 2,
    "amount": 1500.00,
    "is_released": false,
    "release_date": null,
    "created_at": "2023-10-07T10:00:00Z"
  }
  ```

### `POST /api/guarantees/{id}/release/`

- **Descripción**: Acción personalizada que marca la garantía como liberada (`is_released = true`).
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "status": "guarantee released"
  }
  ```

## 7. Endpoints de Incentivos (`/api/incentives/`)

Gestiona los incentivos.

El modelo de `Incentive` en este proyecto contiene: `user` (propietario del incentivo), `amount`, `description`, `created_at`.

### `GET /api/incentives/`

- **Descripción**: Obtiene una lista de todos los incentivos.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "user": 1,
      "amount": 500.00,
      "description": "Incentivo por promoción",
      "created_at": "2023-10-07T10:00:00Z"
    }
  ]
  ```

### `POST /api/incentives/`

- **Descripción**: Crea un nuevo incentivo.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "user": 1,
    "amount": 500.00,
    "description": "Incentivo por promoción"
  }
  ```
  
-- **Response (201 Created)**: Devuelve el incentivo creado con sus campos.

## 8. Endpoints de Pagos (`/api/payments/`)

Gestiona los pagos de alquileres.

El modelo `Payment` contiene: `property`, `tenant`, `amount`, `status` (choices: `pendiente`, `pagado`, `retrasado`), `due_date`, `paid_date`, `fine`, `method` (FK a PaymentMethod), `created_at`, `updated_at`.

### `GET /api/payments/`

- **Descripción**: Obtiene una lista de todos los pagos.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `status`: Filtra por estado del pago (`pendiente`, `pagado`, `retrasado`)
  - `property`: Filtra por ID de propiedad
  - `tenant`: Filtra por ID del inquilino
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "property": 1,
      "tenant": 2,
      "amount": 1500.00,
      "status": "pagado",
      "due_date": "2023-10-07",
      "paid_date": "2023-10-07",
      "fine": 0,
      "method": 1
    }
  ]
  ```

### `POST /api/payments/`

- **Descripción**: Registra un nuevo pago.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "property": 1,
    "tenant": 2,
    "amount": 1500.00,
    "method": 1,
    "due_date": "2023-10-07"
  }
  ```

## 9. Endpoints de Métodos de Pago (`/api/payment-methods/`)

Gestiona los métodos de pago disponibles.

El modelo `PaymentMethod` contiene: `name` y opcionalmente `user` (para métodos asociados a un usuario).

### `GET /api/payment-methods/`

- **Descripción**: Obtiene una lista de todos los métodos de pago.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "name": "Tarjeta de Crédito",
      "user": null
    },
    {
      "id": 2,
      "name": "Transferencia Bancaria",
      "user": null
    }
  ]
  ```

## 10. Endpoints de Reseñas (`/api/reviews/`)

Gestiona las reseñas de propiedades.

### `GET /api/reviews/`

- **Descripción**: Obtiene una lista de todas las reseñas.
- **Autenticación**: No requerida.
- **Parámetros de consulta**:
  - `property`: Filtra por ID de propiedad
  - `rating`: Filtra por calificación (1-5)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "property": 1,
      "user": 2,
      "rating": 5,
      "comment": "Excelente propiedad y ubicación",
      "created_at": "2023-10-07T10:00:00Z"
    }
  ]
  ```

### `POST /api/reviews/`

- **Descripción**: Crea una nueva reseña.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "property": 1,
    "user": 2,
    "rating": 5,
    "comment": "Excelente propiedad y ubicación"
  }
  ```

## 11. Endpoints de Notificaciones (`/api/notifications/`)

Gestiona las notificaciones del sistema.

El modelo `Notification` contiene: `user`, `message`, `is_read`, `created_at`.

### `GET /api/notifications/`

- **Descripción**: Obtiene una lista de todas las notificaciones del usuario autenticado.
- **Autenticación**: Requerida.
- **Parámetros de consulta** (según implementación del ViewSet):
  - `is_read`: Filtra por estado de lectura (`true`/`false`)
  - `user`: Filtra por ID de usuario (si aplica)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "user": 1,
      "message": "Has recibido un nuevo mensaje",
      "is_read": false,
      "created_at": "2023-10-07T10:00:00Z"
    }
  ]
  ```

### `POST /api/notifications/{id}/mark_as_read/`

- **Descripción**: Acción personalizada que marca la notificación como leída. (Nombre de la acción en el ViewSet: `mark_as_read`).
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "status": "notification marked as read"
  }
  ```

## 12. Endpoints de Mensajería (`/api/messages/`)

Gestiona los mensajes entre usuarios.

### `GET /api/messages/`

- **Descripción**: Obtiene una lista de todos los mensajes del usuario autenticado.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "sender": 1,
      "receiver": 2,
      "content": "Hola, ¿la propiedad sigue disponible?",
      "created_at": "2023-10-07T10:00:00Z"
    },
    {
      "id": 2,
      "sender": 2,
      "receiver": 1,
      "content": "Sí, aún está disponible. ¿Te gustaría visitarla?",
      "created_at": "2023-10-07T10:05:00Z"
    }
  ]
  ```

### `POST /api/messages/`

- **Descripción**: Envía un nuevo mensaje.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "receiver": 2,
    "content": "Hola, ¿la propiedad sigue disponible?"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "sender": 1,
    "receiver": 2,
    "content": "Hola, ¿la propiedad sigue disponible?",
    "created_at": "2023-10-07T10:00:00Z"
  }
  ```

### `GET /api/messages/{id}/`

- **Descripción**: Obtiene los detalles de un mensaje específico.
- **Autenticación**: Requerida (solo remitente o destinatario).
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "sender": 1,
    "receiver": 2,
    "content": "Hola, ¿la propiedad sigue disponible?",
    "created_at": "2023-10-07T10:00:00Z"
  }
  ```

> Nota: en la implementación actual no existe una acción `with/{user_id}` en `MessageViewSet`. Si necesitas recuperar el historial entre dos usuarios, filtra el listado de mensajes por `sender`/`receiver` o implementa una acción personalizada.
