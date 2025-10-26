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
- **Descripción**: Registra un nuevo usuario y crea automáticamente su perfil básico.
- **Autenticación**: No requerida (registro público).
- **Content-Type**: `application/json` o `multipart/form-data` (si incluye imagen)
- **Request Body JSON**:
  ```json
  {
    "username": "nuevo_usuario",
    "email": "usuario@example.com",
    "password": "tu_password_segura",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "user_type": "inquilino",
    "phone": "+59112345678"
  }
  ```
- **Request Body Multipart (con imagen)**:
  ```
  Content-Type: multipart/form-data

  username: nuevo_usuario
  email: usuario@example.com
  password: tu_password_segura
  first_name: Nombre
  last_name: Apellido
  user_type: inquilino
  phone: +59112345678
  profile_picture: [archivo de imagen]
  ```
- **Campos opcionales**:
  - `user_type`: Tipo de usuario (`inquilino`, `propietario`, `agente`). Por defecto: `inquilino`
  - `phone`: Número de teléfono. Por defecto: cadena vacía
  - `profile_picture`: Imagen de perfil del usuario (archivo de imagen)
- **Nota sobre Content-Type**:
  - Usa `application/json` para registro sin imagen
  - Usa `multipart/form-data` cuando incluyas `profile_picture`
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
- **Nota**: Al registrar un usuario, se crea automáticamente un perfil básico con los datos proporcionados. Ya no es necesario crear el perfil por separado.

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

### `GET /api/users/me/`
- **Descripción**: Obtiene la información del usuario actual autenticado.
- **Autenticación**: Requerida (JWT Token).
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "username": "usuario1",
    "email": "usuario1@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "date_joined": "2025-10-22T10:00:00Z"
  }
  ```

## 2. Endpoints de Perfiles de Usuario (`/api/profiles/`)

Gestiona los perfiles asociados a los usuarios con información adicional.

**Importante**: Todos los endpoints de perfiles soportan tanto `application/json` como `multipart/form-data`. Usa JSON para datos simples y multipart cuando incluyas archivos de imagen.

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
        "profile_picture": "http://localhost:8000/media/profile_pictures/imagen.jpg",
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
- **Content-Type**: `application/json` o `multipart/form-data`
- **Request Body (JSON)**:
  ```json
  {
    "user_type": "inquilino",
    "phone": "+59112345678",
    "favorites": [1, 2]
  }
  ```
- **Request Body (Multipart con imagen)**:
  ```
  Content-Type: multipart/form-data

  user_type: inquilino
  phone: +59112345678
  profile_picture: [archivo de imagen]
  favorites: [1, 2]
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
    "profile_picture": "http://localhost:8000/media/profile_pictures/imagen.jpg",
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

### `GET /api/profiles/me/`
- **Descripción**: Obtiene el perfil del usuario actual autenticado.
- **Autenticación**: Requerida (JWT Token).
- **Response (200 OK)**:
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
    "profile_picture": "http://localhost:8000/media/profile_pictures/imagen.jpg",
    "is_verified": false,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z",
    "favorites": [1, 2]
  }
  ```
- **Response (404 Not Found)**: Si el usuario no tiene un perfil creado.
  ```json
  {
    "detail": "El usuario no tiene un perfil creado"
  }
  ```

### `PUT/PATCH /api/profiles/{id}/`
- **Descripción**: Actualiza un perfil existente por ID.
- **Autenticación**: Requerida (solo el propio usuario).
- **Content-Type**: `application/json` o `multipart/form-data`
- **Request Body JSON (PATCH)**:
  ```json
  {
    "phone": "+59187654321",
    "user_type": "propietario",
    "favorites": [1, 2, 3, 4]
  }
  ```
- **Request Body Multipart (PATCH)**:
  ```
  Content-Type: multipart/form-data

  phone: +59187654321
  profile_picture: [nueva imagen]
  user_type: propietario
  ```
- **Response (200 OK)**: Devuelve el perfil actualizado.

### `PUT/PATCH /api/profiles/update_me/`
- **Descripción**: Actualiza el perfil del usuario actual autenticado (recomendado).
- **Autenticación**: Requerida (JWT Token).
- **Content-Type**: `application/json` o `multipart/form-data`
- **Request Body JSON (PATCH)**:
  ```json
  {
    "phone": "+59187654321",
    "user_type": "propietario"
  }
  ```
- **Request Body Multipart (PATCH)**:
  ```
  Content-Type: multipart/form-data

  phone: +59187654321
  profile_picture: [nueva imagen]
  user_type: propietario
  ```
- **Response (200 OK)**: Devuelve el perfil actualizado.
- **Response (404 Not Found)**: Si el usuario no tiene perfil.
  ```json
  {
    "detail": "El usuario no tiene un perfil creado"
  }
  ```

### `POST /api/profiles/upload_profile_picture/`
- **Descripción**: Sube o actualiza la foto de perfil del usuario actual.
- **Autenticación**: Requerida (JWT Token).
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `profile_picture`: Archivo de imagen (JPG, PNG, etc.)
- **Response (200 OK)**:
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
    "profile_picture": "http://localhost:8000/media/profile_pictures/nueva_imagen.jpg",
    "is_verified": false,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z",
    "favorites": [1, 2]
  }
  ```
- **Response (400 Bad Request)**: Si no se proporciona imagen.
  ```json
  {
    "detail": "No se proporcionó ninguna imagen"
  }
  ```

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

## Ejemplos Prácticos - Gestión de Fotos de Perfil

### Registro con foto de perfil
```bash
# Registro con imagen usando curl
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: multipart/form-data" \
  -F "username=juan_perez" \
  -F "email=juan@example.com" \
  -F "password=mi_password_seguro" \
  -F "first_name=Juan" \
  -F "last_name=Pérez" \
  -F "user_type=propietario" \
  -F "phone=+59170123456" \
  -F "profile_picture=@/ruta/a/mi_foto.jpg"
```

### Actualizar solo la foto de perfil
```bash
# Subir nueva foto de perfil
curl -X POST http://localhost:8000/api/profiles/upload_profile_picture/ \
  -H "Authorization: Bearer tu_jwt_token" \
  -H "Content-Type: multipart/form-data" \
  -F "profile_picture=@/ruta/a/nueva_foto.jpg"
```

### Actualizar perfil completo con foto
```bash
# Actualizar datos del perfil incluyendo foto
curl -X PATCH http://localhost:8000/api/profiles/update_me/ \
  -H "Authorization: Bearer tu_jwt_token" \
  -H "Content-Type: multipart/form-data" \
  -F "phone=+59170987654" \
  -F "user_type=agente" \
  -F "profile_picture=@/ruta/a/foto_actualizada.jpg"
```

### Actualizar solo datos (sin foto)
```bash
# Actualizar solo datos usando JSON
curl -X PATCH http://localhost:8000/api/profiles/update_me/ \
  -H "Authorization: Bearer tu_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+59170555444",
    "user_type": "inquilino"
  }'
```

### Ver historial de fotos de perfil
```bash
# Obtener historial de fotos del usuario actual
curl -X GET http://localhost:8000/api/profiles/picture_history/ \
  -H "Authorization: Bearer tu_jwt_token"
```

**Respuesta del historial:**
```json
[
  {
    "id": 3,
    "image": "http://localhost:8000/media/profile_pictures/user_1_20241201_143022_a1b2c3d4.jpg",
    "original_filename": "nueva_foto.jpg",
    "uploaded_at": "2024-12-01T14:30:22.123456Z",
    "is_current": true
  },
  {
    "id": 2,
    "image": "http://localhost:8000/media/profile_pictures/user_1_20241130_091545_e5f6g7h8.jpg",
    "original_filename": "foto_anterior.jpg",
    "uploaded_at": "2024-11-30T09:15:45.987654Z",
    "is_current": false
  },
  {
    "id": 1,
    "image": "http://localhost:8000/media/profile_pictures/user_1_20241129_160312_i9j0k1l2.jpg",
    "original_filename": "primera_foto.jpg",
    "uploaded_at": "2024-11-29T16:03:12.456789Z",
    "is_current": false
  }
]
```

**Notas importantes:**
- Las imágenes se almacenan en `media/profile_pictures/` con nombres únicos
- Formato de nombres: `user_{id}_{timestamp}_{uuid}.{extension}`
- Se mantiene un historial completo de todas las fotos subidas
- Solo una foto puede estar marcada como `is_current: true`
- Formatos soportados: JPG, PNG, GIF, WEBP
- Tamaño máximo recomendado: 5MB
- Las URLs de las imágenes incluyen el dominio completo en las respuestas

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

### `GET /api/incentives/active/`
- **Descripción**: Obtiene los incentivos activos del usuario autenticado.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "user": 1,
      "zone": {
        "id": 1,
        "name": "Centro"
      },
      "amount": "500.00",
      "description": "Incentivo por alta demanda en Centro",
      "incentive_type": "high_demand",
      "is_active": true,
      "valid_until": "2025-11-22T10:00:00Z",
      "created_at": "2025-10-22T10:00:00Z"
    }
  ]
  ```

### `GET /api/incentives/by_zone/?zone_id={zone_id}`
- **Descripción**: Obtiene los incentivos del usuario filtrados por zona específica.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `zone_id` (requerido): ID de la zona
- **Response (200 OK)**: Lista de incentivos para la zona especificada.

### `POST /api/incentives/{id}/use/`
- **Descripción**: Marca un incentivo como usado (lo desactiva).
- **Autenticación**: Requerida (solo el propietario del incentivo).
- **Response (200 OK)**:
  ```json
  {
    "message": "Incentive used successfully",
    "incentive": {
      "id": 1,
      "user": 1,
      "amount": "500.00",
      "description": "Incentivo por alta demanda",
      "is_active": false,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```

## 8. Endpoints de Reglas de Incentivos (`/api/incentive-rules/`)

Gestiona las reglas para la generación automática de incentivos (solo administradores).

### `GET /api/incentive-rules/`
- **Descripción**: Lista todas las reglas de incentivos.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "Alta Demanda",
        "description": "Incentivo cuando la demanda supera significativamente la oferta",
        "incentive_type": "high_demand",
        "min_demand_count": 10,
        "max_offer_demand_ratio": 0.5,
        "base_amount": "300.00",
        "percentage_bonus": 0.1,
        "duration_days": 30,
        "cooldown_days": 7,
        "is_active": true,
        "created_at": "2025-10-22T10:00:00Z"
      }
    ]
  }
  ```

### `POST /api/incentive-rules/generate_incentives/`
- **Descripción**: Genera incentivos automáticos manualmente (solo administradores).
- **Autenticación**: Requerida (solo administradores).
- **Request Body (opcional)**:
  ```json
  {
    "zone_id": 1
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "message": "Generated 5 incentives for Centro",
    "incentives_count": 5,
    "timestamp": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/incentive-rules/market_analysis/?zone_id={zone_id}`
- **Descripción**: Obtiene análisis de mercado para zonas específicas o todas las zonas.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `zone_id` (opcional): ID de zona específica. Si no se proporciona, analiza todas las zonas.
- **Response para zona específica (200 OK)**:
  ```json
  {
    "zone": {
      "id": 1,
      "name": "Centro",
      "offer_count": 15,
      "demand_count": 25
    },
    "conditions": {
      "offer_demand_ratio": 0.6,
      "activity_score": 8.5,
      "high_demand": true,
      "low_supply": false,
      "low_activity": false,
      "needs_incentives": true
    },
    "timestamp": "2025-10-22T10:00:00Z"
  }
  ```
- **Response para todas las zonas (200 OK)**:
  ```json
  {
    "zones_analysis": [
      {
        "zone": {
          "id": 1,
          "name": "Centro",
          "offer_count": 15,
          "demand_count": 25
        },
        "conditions": {
          "offer_demand_ratio": 0.6,
          "activity_score": 8.5,
          "high_demand": true,
          "low_supply": false,
          "low_activity": false,
          "needs_incentives": true
        }
      }
    ],
    "timestamp": "2025-10-22T10:00:00Z"
  }
  ```

### `POST /api/incentive-rules/{id}/toggle_active/`
- **Descripción**: Activa o desactiva una regla de incentivo (solo administradores).
- **Autenticación**: Requerida (solo administradores).
- **Response (200 OK)**:
  ```json
  {
    "message": "Rule activated successfully",
    "rule": {
      "id": 1,
      "name": "Alta Demanda",
      "is_active": true,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```

## 9. Endpoints de Zonas (`/api/zones/`)

Gestiona las zonas geográficas con funcionalidades GIS y estadísticas de mercado.

### `GET /api/zones/`
- **Descripción**: Lista todas las zonas con información básica.
- **Autenticación**: No requerida.
- **Parámetros de consulta**:
  - `name`: Filtra por nombre de zona
- **Response (200 OK)**:
  ```json
  {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "Centro",
        "description": "Zona céntrica de la ciudad",
        "offer_count": 15,
        "demand_count": 25,
        "avg_price": "1200.00",
        "created_at": "2025-10-22T10:00:00Z",
        "updated_at": "2025-10-22T12:00:00Z"
      }
    ]
  }
  ```

### `POST /api/zones/`
- **Descripción**: Crea una nueva zona (solo administradores).
- **Autenticación**: Requerida (solo administradores).
- **Request Body**:
  ```json
  {
    "name": "Zona Norte",
    "description": "Zona residencial al norte de la ciudad",
    "bounds": {
      "type": "Polygon",
      "coordinates": [[
        [-63.1821, -17.7834],
        [-63.1800, -17.7834],
        [-63.1800, -17.7800],
        [-63.1821, -17.7800],
        [-63.1821, -17.7834]
      ]]
    }
  }
  ```

### `GET /api/zones/{id}/`
- **Descripción**: Obtiene detalles de una zona específica.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "name": "Centro",
    "description": "Zona céntrica de la ciudad",
    "bounds": {
      "type": "Polygon",
      "coordinates": [...]
    },
    "offer_count": 15,
    "demand_count": 25,
    "avg_price": "1200.00",
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T12:00:00Z"
  }
  ```

### `GET /api/zones/stats/`
- **Descripción**: Obtiene estadísticas agregadas de todas las zonas.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "total_zones": 10,
    "total_properties": 150,
    "total_demand": 300,
    "avg_price_all_zones": "1150.00",
    "zones_with_high_demand": 3,
    "zones_with_low_supply": 2,
    "last_updated": "2025-10-22T12:00:00Z"
  }
  ```

### `GET /api/zones/{id}/stats/`
- **Descripción**: Obtiene estadísticas detalladas de una zona específica.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "zone": {
      "id": 1,
      "name": "Centro"
    },
    "property_count": 15,
    "offer_count": 15,
    "demand_count": 25,
    "supply_demand_ratio": 0.6,
    "avg_price": "1200.00",
    "price_range": {
      "min": "800.00",
      "max": "2000.00"
    },
    "recent_activity": {
      "searches_last_30_days": 45,
      "new_properties_last_30_days": 3,
      "favorites_count": 12
    },
    "market_conditions": {
      "high_demand": true,
      "low_supply": false,
      "activity_score": 8.5
    },
    "last_updated": "2025-10-22T12:00:00Z"
  }
  ```

### `GET /api/zones/heatmap/`
- **Descripción**: Obtiene datos para generar un mapa de calor de actividad por zonas.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "heatmap_data": [
      {
        "zone_id": 1,
        "name": "Centro",
        "center_lat": -17.7834,
        "center_lng": -63.1821,
        "activity_score": 8.5,
        "demand_intensity": 0.85,
        "supply_intensity": 0.45,
        "price_level": "high"
      }
    ],
    "legend": {
      "activity_score": "Puntuación de actividad (0-10)",
      "demand_intensity": "Intensidad de demanda (0-1)",
      "supply_intensity": "Intensidad de oferta (0-1)",
      "price_level": "Nivel de precios (low/medium/high)"
    }
  }
  ```

### `GET /api/zones/geojson/`
- **Descripción**: Obtiene todas las zonas en formato GeoJSON para mapas.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [[
            [-63.1821, -17.7834],
            [-63.1800, -17.7834],
            [-63.1800, -17.7800],
            [-63.1821, -17.7800],
            [-63.1821, -17.7834]
          ]]
        },
        "properties": {
          "id": 1,
          "name": "Centro",
          "offer_count": 15,
          "demand_count": 25,
          "avg_price": "1200.00",
          "activity_score": 8.5
        }
      }
    ]
  }
  ```

### `POST /api/zones/search_log/`
- **Descripción**: Registra una búsqueda realizada en una zona específica.
- **Autenticación**: No requerida.
- **Request Body**:
  ```json
  {
    "zone": 1,
    "search_query": "departamento 2 dormitorios",
    "user_ip": "192.168.1.1"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "zone": 1,
    "search_query": "departamento 2 dormitorios",
    "user_ip": "192.168.1.1",
    "created_at": "2025-10-22T10:00:00Z"
  }
  ```

### `GET /api/zones/{id}/nearby_zones/?distance_km={distance}`
- **Descripción**: Obtiene zonas cercanas a una zona específica.
- **Autenticación**: No requerida.
- **Parámetros de consulta**:
  - `distance_km` (opcional): Distancia en kilómetros (por defecto: 5)
- **Response (200 OK)**:
  ```json
  {
    "zone": {
      "id": 1,
      "name": "Centro"
    },
    "nearby_zones": [
      {
        "id": 2,
        "name": "Zona Norte",
        "distance_km": 2.5,
        "offer_count": 8,
        "demand_count": 12,
        "avg_price": "950.00"
      }
    ],
    "search_radius_km": 5
  }
  ```

### `GET /api/zones/find_by_location/?lat={latitude}&lng={longitude}`
- **Descripción**: Encuentra la zona que contiene una ubicación específica.
- **Autenticación**: No requerida.
- **Parámetros de consulta**:
  - `lat` (requerido): Latitud
  - `lng` (requerido): Longitud
- **Response (200 OK)**:
  ```json
  {
    "zone": {
      "id": 1,
      "name": "Centro",
      "description": "Zona céntrica de la ciudad",
      "offer_count": 15,
      "demand_count": 25,
      "avg_price": "1200.00"
    },
    "coordinates": {
      "lat": -17.7834,
      "lng": -63.1821
    }
  }
  ```

## 10. Endpoints de Pagos (`/api/payments/`)

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
