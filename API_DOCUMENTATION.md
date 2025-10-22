# Documentación de la API de Habitto

Este documento describe los endpoints de la API del proyecto Habitto.

## Base URL
- **Desarrollo**: `http://localhost:8000`
- **Producción**: `https://tu-dominio.com`

## Autenticación

La mayoría de los endpoints requieren autenticación por JWT. Para autenticarte, primero obtén un token usando el endpoint de login:

### `POST /api/login/`
- **Descripción**: Obtiene un par de tokens JWT (access y refresh).
- **Request Body**:
  ```json
  {
    "username": "usuario",
    "password": "tu_password_segura"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

### `POST /api/refresh/`
- **Descripción**: Refresca el token de acceso usando el refresh token.
- **Request Body**:
  ```json
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

**Incluye el token en la cabecera de tus peticiones:**
```
Authorization: Bearer <access_token>
```

## Paginación

Todos los endpoints de listado utilizan paginación automática con los siguientes parámetros:
- **page**: Número de página (por defecto: 1)
- **page_size**: Elementos por página (por defecto: 20)

**Respuesta paginada:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/properties/?page=2",
  "previous": null,
  "results": [...]
}
```

## 1. Endpoints de Usuarios (`/api/users/`)

Gestiona los usuarios del sistema usando el modelo User de Django.

### `POST /api/users/`
- **Descripción**: Registra un nuevo usuario.
- **Autenticación**: No requerida (registro público).
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
    "date_joined": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/users/`
- **Descripción**: Obtiene una lista paginada de todos los usuarios.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "count": 25,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "username": "usuario1",
        "email": "usuario1@example.com",
        "first_name": "Nombre1",
        "last_name": "Apellido1",
        "date_joined": "2025-10-22T10:00:00Z"
      }
    ]
  }
  ```

### `GET /api/users/{id}/`
- **Descripción**: Obtiene los detalles de un usuario específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "username": "usuario1",
    "email": "usuario1@example.com",
    "first_name": "Nombre1",
    "last_name": "Apellido1",
    "date_joined": "2025-10-22T10:00:00Z"
  }
  ```

### `PUT/PATCH /api/users/{id}/`
- **Descripción**: Actualiza un usuario existente.
- **Autenticación**: Requerida (solo el propio usuario).
- **Request Body (PATCH)**:
  ```json
  {
    "first_name": "Nuevo Nombre",
    "last_name": "Nuevo Apellido"
  }
  ```
- **Response (200 OK)**: Devuelve el usuario actualizado.

### `DELETE /api/users/{id}/`
- **Descripción**: Elimina un usuario.
- **Autenticación**: Requerida (solo el propio usuario o admin).
- **Response (204 No Content)**: Sin contenido en la respuesta.

## 2. Endpoints de Perfiles de Usuario (`/api/profiles/`)

Gestiona los perfiles asociados a los usuarios con información adicional.

### `GET /api/profiles/`
- **Descripción**: Obtiene una lista paginada de perfiles de usuario.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "count": 15,
    "next": "http://localhost:8000/api/profiles/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "user": {
          "id": 1,
          "username": "usuario1",
          "email": "usuario1@example.com",
          "first_name": "Juan",
          "last_name": "Pérez",
          "date_joined": "2025-10-22T10:00:00Z"
        },
        "user_type": "inquilino",
        "phone": "+59112345678",
        "is_verified": false,
        "created_at": "2025-10-22T10:00:00Z",
        "updated_at": "2025-10-22T10:00:00Z",
        "favorites": [1, 3, 5]
      }
    ]
  }
  ```

### `POST /api/profiles/`
- **Descripción**: Crea un perfil para el usuario autenticado.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "user_type": "inquilino",
    "phone": "+59112345678",
    "favorites": [1, 2]
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "user": {
      "id": 1,
      "username": "usuario1",
      "email": "usuario1@example.com",
      "first_name": "Juan",
      "last_name": "Pérez",
      "date_joined": "2025-10-22T10:00:00Z"
    },
    "user_type": "inquilino",
    "phone": "+59112345678",
    "is_verified": false,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z",
    "favorites": [1, 2]
  }
  ```

### `GET /api/profiles/{id}/`
- **Descripción**: Obtiene los detalles de un perfil específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/profiles/{id}/`
- **Descripción**: Actualiza un perfil existente.
- **Autenticación**: Requerida (solo el propio usuario).
- **Request Body (PATCH)**:
  ```json
  {
    "phone": "+59187654321",
    "favorites": [1, 2, 3, 4]
  }
  ```
- **Response (200 OK)**: Devuelve el perfil actualizado.

### `POST /api/profiles/{id}/verify/`
- **Descripción**: Acción personalizada que marca un perfil como verificado.
- **Autenticación**: Requerida (solo administradores).
- **Response (200 OK)**:
  ```json
  {
    "status": "verified"
  }
  ```

### `DELETE /api/profiles/{id}/`
- **Descripción**: Elimina un perfil.
- **Autenticación**: Requerida (solo el propio usuario o admin).
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Tipos de usuario disponibles:**
- `inquilino`: Usuario que busca propiedades para alquilar
- `propietario`: Usuario que publica propiedades
- `agente`: Usuario que gestiona propiedades de terceros

## 3. Endpoints de Propiedades (`/api/properties/`)

Gestiona las propiedades inmobiliarias del sistema.

### `GET /api/properties/`
- **Descripción**: Obtiene una lista paginada de propiedades con opciones de filtrado, búsqueda y ordenamiento.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `type`: Filtra por tipo de propiedad (`casa`, `departamento`, `habitacion`, `anticretico`)
  - `is_active`: Filtra por estado de la propiedad (`true`/`false`)
  - `owner`: Filtra por ID del propietario
  - `search`: Búsqueda en dirección y descripción
  - `ordering`: Ordena por `price` o `created_at` (prefija con `-` para orden descendente)
  - `page`: Número de página
  - `page_size`: Elementos por página
- **Response (200 OK)**:
  ```json
  {
    "count": 50,
    "next": "http://localhost:8000/api/properties/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "owner": 1,
        "agent": null,
        "type": "casa",
        "address": "Calle Falsa 123, La Paz",
        "latitude": "-16.500000",
        "longitude": "-68.150000",
        "price": "1500.00",
        "guarantee": "1500.00",
        "description": "Casa amplia en zona residencial con jardín",
        "size": 120.5,
        "bedrooms": 3,
        "bathrooms": 2,
        "amenities": [1, 2, 3],
        "availability_date": "2025-11-01",
        "is_active": true,
        "created_at": "2025-10-22T10:00:00Z",
        "updated_at": "2025-10-22T10:00:00Z",
        "accepted_payment_methods": [1, 2]
      }
    ]
  }
  ```

### `POST /api/properties/`
- **Descripción**: Crea una nueva propiedad.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "owner": 1,
    "agent": null,
    "type": "casa",
    "address": "Calle Falsa 123, La Paz",
    "latitude": "-16.500000",
    "longitude": "-68.150000",
    "price": "1500.00",
    "guarantee": "1500.00",
    "description": "Casa amplia en zona residencial con jardín",
    "size": 120.5,
    "bedrooms": 3,
    "bathrooms": 2,
    "amenities": [1, 2, 3],
    "availability_date": "2025-11-01",
    "accepted_payment_methods": [1, 2]
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "owner": 1,
    "agent": null,
    "type": "casa",
    "address": "Calle Falsa 123, La Paz",
    "latitude": "-16.500000",
    "longitude": "-68.150000",
    "price": "1500.00",
    "guarantee": "1500.00",
    "description": "Casa amplia en zona residencial con jardín",
    "size": 120.5,
    "bedrooms": 3,
    "bathrooms": 2,
    "amenities": [1, 2, 3],
    "availability_date": "2025-11-01",
    "is_active": true,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z",
    "accepted_payment_methods": [1, 2]
  }
  ```

### `GET /api/properties/{id}/`
- **Descripción**: Obtiene los detalles de una propiedad específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/properties/{id}/`
- **Descripción**: Actualiza una propiedad existente.
- **Autenticación**: Requerida (solo propietario o agente asignado).
- **Request Body (PATCH)**:
  ```json
  {
    "price": "1800.00",
    "description": "Casa amplia en zona residencial con jardín y piscina",
    "amenities": [1, 2, 3, 4]
  }
  ```
- **Response (200 OK)**: Devuelve la propiedad actualizada.

### `DELETE /api/properties/{id}/`
- **Descripción**: Elimina una propiedad.
- **Autenticación**: Requerida (solo propietario o administrador).
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Tipos de propiedad disponibles:**
- `casa`: Casa independiente
- `departamento`: Departamento o apartamento
- `habitacion`: Habitación individual
- `anticretico`: Propiedad en anticrético (modalidad boliviana)

## 4. Endpoints de Fotos (`/api/photos/`)

Gestiona las fotos de las propiedades.

### `GET /api/photos/`
- **Descripción**: Obtiene una lista paginada de todas las fotos de propiedades.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `property`: Filtra por ID de propiedad
  - `page`: Número de página
  - `page_size`: Elementos por página
- **Response (200 OK)**:
  ```json
  {
    "count": 25,
    "next": "http://localhost:8000/api/photos/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "property": 1,
        "image": "http://localhost:8000/media/properties/foto1.jpg",
        "caption": "Fachada de la propiedad",
        "created_at": "2025-10-22T10:00:00Z"
      },
      {
        "id": 2,
        "property": 1,
        "image": "http://localhost:8000/media/properties/foto2.jpg",
        "caption": "Sala de estar",
        "created_at": "2025-10-22T11:00:00Z"
      }
    ]
  }
  ```

### `POST /api/photos/`
- **Descripción**: Sube una nueva foto para una propiedad.
- **Autenticación**: Requerida.
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `property` (obligatorio): ID de la propiedad
  - `image` (obligatorio): Archivo de imagen (JPG, PNG, etc.)
  - `caption` (opcional): Descripción de la foto
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "image": "http://localhost:8000/media/properties/foto1.jpg",
    "caption": "Fachada de la propiedad",
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/photos/{id}/`
- **Descripción**: Obtiene los detalles de una foto específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/photos/{id}/`
- **Descripción**: Actualiza una foto (solo caption, no se puede cambiar la imagen).
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Request Body (PATCH)**:
  ```json
  {
    "caption": "Nueva descripción de la foto"
  }
  ```
- **Response (200 OK)**: Devuelve la foto actualizada.

### `DELETE /api/photos/{id}/`
- **Descripción**: Elimina una foto.
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Nota**: Las imágenes se almacenan en el directorio `media/properties/` del servidor.

## 5. Endpoints de Amenidades (`/api/amenities/`)

Gestiona las amenidades disponibles para las propiedades.

### `GET /api/amenities/`
- **Descripción**: Obtiene una lista paginada de todas las amenidades disponibles.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "Piscina"
      },
      {
        "id": 2,
        "name": "Gimnasio"
      },
      {
        "id": 3,
        "name": "Garaje"
      },
      {
        "id": 4,
        "name": "Jardín"
      }
    ]
  }
  ```

### `POST /api/amenities/`
- **Descripción**: Crea una nueva amenidad.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "name": "Sauna"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 5,
    "name": "Sauna"
  }
  ```

### `GET /api/amenities/{id}/`
- **Descripción**: Obtiene los detalles de una amenidad específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/amenities/{id}/`
- **Descripción**: Actualiza una amenidad existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "name": "Piscina Climatizada"
  }
  ```
- **Response (200 OK)**: Devuelve la amenidad actualizada.

### `DELETE /api/amenities/{id}/`
- **Descripción**: Elimina una amenidad.
- **Autenticación**: Requerida.
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Ejemplos de amenidades comunes:**
- Piscina, Gimnasio, Garaje, Jardín, Balcón, Terraza, Amueblado, Internet, Cable, Seguridad 24h

## 6. Endpoints de Garantías (`/api/guarantees/`)

Gestiona las garantías de depósito de las propiedades.

### `GET /api/guarantees/`
- **Descripción**: Obtiene una lista paginada de todas las garantías.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `property`: Filtra por ID de propiedad
  - `tenant`: Filtra por ID del inquilino
  - `is_released`: Filtra por estado de liberación (`true`/`false`)
- **Response (200 OK)**:
  ```json
  {
    "count": 15,
    "next": "http://localhost:8000/api/guarantees/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "property": 1,
        "tenant": 2,
        "amount": "1500.00",
        "is_released": false,
        "release_date": null,
        "created_at": "2025-10-22T10:00:00Z"
      }
    ]
  }
  ```

### `POST /api/guarantees/`
- **Descripción**: Crea una nueva garantía.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "property": 1,
    "tenant": 2,
    "amount": "1500.00"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "tenant": 2,
    "amount": "1500.00",
    "is_released": false,
    "release_date": null,
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/guarantees/{id}/`
- **Descripción**: Obtiene los detalles de una garantía específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/guarantees/{id}/`
- **Descripción**: Actualiza una garantía existente.
- **Autenticación**: Requerida (solo propietario o inquilino involucrado).
- **Request Body (PATCH)**:
  ```json
  {
    "amount": "1800.00"
  }
  ```
- **Response (200 OK)**: Devuelve la garantía actualizada.

### `POST /api/guarantees/{id}/release/`
- **Descripción**: Acción personalizada que libera la garantía.
- **Autenticación**: Requerida (solo propietario).
- **Response (200 OK)**:
  ```json
  {
    "status": "guarantee released"
  }
  ```

### `DELETE /api/guarantees/{id}/`
- **Descripción**: Elimina una garantía.
- **Autenticación**: Requerida (solo propietario o admin).
- **Response (204 No Content)**: Sin contenido en la respuesta.

## 7. Endpoints de Incentivos (`/api/incentives/`)

Gestiona los incentivos económicos para usuarios.

### `GET /api/incentives/`
- **Descripción**: Obtiene una lista paginada de todos los incentivos.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `user`: Filtra por ID del usuario
- **Response (200 OK)**:
  ```json
  {
    "count": 8,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "user": 1,
        "amount": "500.00",
        "description": "Incentivo por referir nuevo usuario",
        "created_at": "2025-10-22T10:00:00Z"
      },
      {
        "id": 2,
        "user": 1,
        "amount": "200.00",
        "description": "Bono por primera publicación",
        "created_at": "2025-10-22T11:00:00Z"
      }
    ]
  }
  ```

### `POST /api/incentives/`
- **Descripción**: Crea un nuevo incentivo.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "user": 1,
    "amount": "500.00",
    "description": "Incentivo por referir nuevo usuario"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "user": 1,
    "amount": "500.00",
    "description": "Incentivo por referir nuevo usuario",
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/incentives/{id}/`
- **Descripción**: Obtiene los detalles de un incentivo específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/incentives/{id}/`
- **Descripción**: Actualiza un incentivo existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "description": "Incentivo por referir nuevo usuario - Actualizado"
  }
  ```
- **Response (200 OK)**: Devuelve el incentivo actualizado.

### `DELETE /api/incentives/{id}/`
- **Descripción**: Elimina un incentivo.
- **Autenticación**: Requerida.
- **Response (204 No Content)**: Sin contenido en la respuesta.

## 8. Endpoints de Pagos (`/api/payments/`)

Gestiona los pagos de alquileres y rentas.

### `GET /api/payments/`
- **Descripción**: Obtiene una lista paginada de todos los pagos.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `status`: Filtra por estado (`pendiente`, `pagado`, `retrasado`)
  - `property`: Filtra por ID de propiedad
  - `tenant`: Filtra por ID del inquilino
  - `due_date`: Filtra por fecha de vencimiento
- **Response (200 OK)**:
  ```json
  {
    "count": 30,
    "next": "http://localhost:8000/api/payments/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "property": 1,
        "tenant": 2,
        "amount": "1500.00",
        "status": "pagado",
        "due_date": "2025-10-07",
        "paid_date": "2025-10-07",
        "fine": "0.00",
        "method": 1,
        "created_at": "2025-10-22T10:00:00Z",
        "updated_at": "2025-10-22T10:00:00Z"
      }
    ]
  }
  ```

### `POST /api/payments/`
- **Descripción**: Registra un nuevo pago.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "property": 1,
    "tenant": 2,
    "amount": "1500.00",
    "due_date": "2025-11-07",
    "method": 1
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "tenant": 2,
    "amount": "1500.00",
    "status": "pendiente",
    "due_date": "2025-11-07",
    "paid_date": null,
    "fine": "0.00",
    "method": 1,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/payments/{id}/`
- **Descripción**: Obtiene los detalles de un pago específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/payments/{id}/`
- **Descripción**: Actualiza un pago existente (ej: marcar como pagado).
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "status": "pagado",
    "paid_date": "2025-10-22"
  }
  ```
- **Response (200 OK)**: Devuelve el pago actualizado.

### `DELETE /api/payments/{id}/`
- **Descripción**: Elimina un pago.
- **Autenticación**: Requerida.
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Estados de pago disponibles:**
- `pendiente`: Pago aún no realizado
- `pagado`: Pago completado
- `retrasado`: Pago vencido sin completar

## 9. Endpoints de Métodos de Pago (`/api/payment-methods/`)

Gestiona los métodos de pago disponibles en el sistema.

### `GET /api/payment-methods/`
- **Descripción**: Obtiene una lista paginada de todos los métodos de pago.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `user`: Filtra por ID del usuario (métodos personalizados)
- **Response (200 OK)**:
  ```json
  {
    "count": 8,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "Efectivo",
        "user": null
      },
      {
        "id": 2,
        "name": "Transferencia Bancaria",
        "user": null
      },
      {
        "id": 3,
        "name": "Tarjeta de Crédito Visa",
        "user": 1
      }
    ]
  }
  ```

### `POST /api/payment-methods/`
- **Descripción**: Crea un nuevo método de pago.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "name": "PayPal",
    "user": null
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 4,
    "name": "PayPal",
    "user": null
  }
  ```

### `GET /api/payment-methods/{id}/`
- **Descripción**: Obtiene los detalles de un método de pago específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/payment-methods/{id}/`
- **Descripción**: Actualiza un método de pago existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "name": "PayPal Empresarial"
  }
  ```
- **Response (200 OK)**: Devuelve el método de pago actualizado.

### `DELETE /api/payment-methods/{id}/`
- **Descripción**: Elimina un método de pago.
- **Autenticación**: Requerida.
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Nota**: Los métodos de pago pueden ser globales (`user: null`) o específicos de un usuario.

## 10. Endpoints de Reseñas (`/api/reviews/`)

Gestiona las reseñas y calificaciones de propiedades.

### `GET /api/reviews/`
- **Descripción**: Obtiene una lista paginada de todas las reseñas.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `property`: Filtra por ID de propiedad
  - `user`: Filtra por ID del usuario que escribió la reseña
  - `rating`: Filtra por calificación específica
- **Response (200 OK)**:
  ```json
  {
    "count": 45,
    "next": "http://localhost:8000/api/reviews/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "property": 1,
        "user": 2,
        "rating": 5,
        "comment": "Excelente propiedad, muy bien ubicada y en perfecto estado",
        "created_at": "2025-10-22T10:00:00Z"
      },
      {
        "id": 2,
        "property": 1,
        "user": 3,
        "rating": 4,
        "comment": "Buena propiedad, solo le falta un poco más de iluminación",
        "created_at": "2025-10-22T11:00:00Z"
      }
    ]
  }
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
    "comment": "Excelente propiedad, muy bien ubicada y en perfecto estado"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "property": 1,
    "user": 2,
    "rating": 5,
    "comment": "Excelente propiedad, muy bien ubicada y en perfecto estado",
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/reviews/{id}/`
- **Descripción**: Obtiene los detalles de una reseña específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/reviews/{id}/`
- **Descripción**: Actualiza una reseña existente.
- **Autenticación**: Requerida (solo el autor de la reseña).
- **Request Body (PATCH)**:
  ```json
  {
    "rating": 4,
    "comment": "Buena propiedad, actualizo mi comentario después de vivir aquí"
  }
  ```
- **Response (200 OK)**: Devuelve la reseña actualizada.

### `DELETE /api/reviews/{id}/`
- **Descripción**: Elimina una reseña.
- **Autenticación**: Requerida (solo el autor o admin).
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Escala de calificación**: 1-5 estrellas (1 = Muy malo, 5 = Excelente)

## 11. Endpoints de Notificaciones (`/api/notifications/`)

Gestiona las notificaciones del sistema para los usuarios.

### `GET /api/notifications/`
- **Descripción**: Obtiene una lista paginada de notificaciones.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `user`: Filtra por ID de usuario
  - `is_read`: Filtra por estado de lectura (`true`/`false`)
- **Response (200 OK)**:
  ```json
  {
    "count": 12,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "user": 1,
        "message": "Has recibido un nuevo mensaje de Juan sobre la propiedad en Calle Falsa 123",
        "is_read": false,
        "created_at": "2025-10-22T10:00:00Z"
      },
      {
        "id": 2,
        "user": 1,
        "message": "Tu pago de alquiler vence en 3 días",
        "is_read": true,
        "created_at": "2025-10-22T09:00:00Z"
      }
    ]
  }
  ```

### `POST /api/notifications/`
- **Descripción**: Crea una nueva notificación.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "user": 1,
    "message": "Tu pago de alquiler vence mañana"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 3,
    "user": 1,
    "message": "Tu pago de alquiler vence mañana",
    "is_read": false,
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/notifications/{id}/`
- **Descripción**: Obtiene los detalles de una notificación específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/notifications/{id}/`
- **Descripción**: Actualiza una notificación existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "is_read": true
  }
  ```
- **Response (200 OK)**: Devuelve la notificación actualizada.

### `POST /api/notifications/{id}/mark_as_read/`
- **Descripción**: Acción personalizada que marca la notificación como leída.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "status": "notification marked as read"
  }
  ```

### `DELETE /api/notifications/{id}/`
- **Descripción**: Elimina una notificación.
- **Autenticación**: Requerida.
- **Response (204 No Content)**: Sin contenido en la respuesta.

## 12. Endpoints de Mensajería (`/api/messages/`)

Gestiona los mensajes entre usuarios del sistema.

### `GET /api/messages/`
- **Descripción**: Obtiene una lista paginada de mensajes.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `sender`: Filtra por ID del remitente
  - `receiver`: Filtra por ID del destinatario
- **Response (200 OK)**:
  ```json
  {
    "count": 25,
    "next": "http://localhost:8000/api/messages/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "sender": 1,
        "receiver": 2,
        "content": "Hola, estoy interesado en la propiedad que publicaste en Calle Falsa 123",
        "created_at": "2025-10-22T10:00:00Z"
      },
      {
        "id": 2,
        "sender": 2,
        "receiver": 1,
        "content": "¡Hola! Sí, la propiedad sigue disponible. ¿Te gustaría programar una visita?",
        "created_at": "2025-10-22T10:05:00Z"
      }
    ]
  }
  ```

### `POST /api/messages/`
- **Descripción**: Envía un nuevo mensaje.
- **Autenticación**: Requerida.
- **Request Body**:
  ```json
  {
    "sender": 1,
    "receiver": 2,
    "content": "Hola, estoy interesado en la propiedad que publicaste"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "sender": 1,
    "receiver": 2,
    "content": "Hola, estoy interesado en la propiedad que publicaste",
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/messages/{id}/`
- **Descripción**: Obtiene los detalles de un mensaje específico.
- **Autenticación**: Requerida (solo remitente o destinatario).
- **Response (200 OK)**: Igual estructura que POST response.

### `PUT/PATCH /api/messages/{id}/`
- **Descripción**: Actualiza un mensaje existente.
- **Autenticación**: Requerida (solo el remitente).
- **Request Body (PATCH)**:
  ```json
  {
    "content": "Hola, estoy muy interesado en la propiedad que publicaste"
  }
  ```
- **Response (200 OK)**: Devuelve el mensaje actualizado.

### `DELETE /api/messages/{id}/`
- **Descripción**: Elimina un mensaje.
- **Autenticación**: Requerida (solo el remitente o admin).
- **Response (204 No Content)**: Sin contenido en la respuesta.

**Consejos para obtener conversaciones:**
- Para obtener mensajes entre dos usuarios específicos, usa: `/api/messages/?sender=1&receiver=2` y `/api/messages/?sender=2&receiver=1`
- Ordena por `created_at` para mostrar cronológicamente
