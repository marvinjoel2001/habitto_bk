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
- **Autenticación**: Opcional (lectura pública). Si el usuario está autenticado, se habilitan filtros basados en su `SearchProfile` como `match_score`.
- **Parámetros de consulta**:
  - `type`: Filtra por tipo de propiedad (`casa`, `departamento`, `habitacion`, `anticretico`)
  - `is_active`: Filtra por estado de la propiedad (`true`/`false`)
  - `owner`: Filtra por ID del propietario
  - `search`: Búsqueda en dirección y descripción
  - `ordering`: Ordena por `price` o `created_at` (prefija con `-` para orden descendente)
  - `page`: Número de página
  - `page_size`: Elementos por página
  - `match_score`: Umbral de score de matching (0–100). Si el usuario autenticado tiene `SearchProfile`, se devuelven solo propiedades con score >= `match_score` respecto a su perfil.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Propiedades obtenidas exitosamente",
    "data": {
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
          "accepted_payment_methods": [1, 2],
          "allows_roommates": false,
          "max_occupancy": 3,
          "min_price_per_person": "500.00",
          "is_furnished": false,
          "tenant_requirements": {"no_smoking": true},
          "tags": ["céntrico", "luminoso"],
          "semantic_embedding": null
        }
      ]
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Parámetros de consulta inválidos",
      "data": null
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "success": false,
      "message": "Token de autenticación requerido",
      "data": null
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para acceder a este recurso",
      "data": null
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "success": false,
      "message": "Error interno del servidor",
      "data": null
    }
    ```

### `POST /api/properties/`
- **Descripción**: Crea una nueva propiedad usando coordenadas geográficas (PointField).
- **Autenticación**: Requerida.
- **Nota importante**: El sistema utiliza un `PointField` para almacenar la ubicación. Debes proporcionar `latitude` y `longitude` como campos separados, que se convertirán automáticamente en un punto geográfico.
 - **Nota de salida**: `latitude` y `longitude` son write-only durante la creación y no aparecen en la respuesta. La respuesta incluye el `id` de la nueva propiedad para usarlo en pasos posteriores (por ejemplo, subir fotos).
- **Request Body**:
  ```json
  {
    "type": "casa",
    "address": "Calle Falsa 123, La Paz",
    "latitude": "-16.5000000000",
    "longitude": "-68.1500000000",
    "price": "1500.00",
    "guarantee": "1500.00",
    "description": "Casa amplia en zona residencial con jardín",
    "size": 120.5,
    "bedrooms": 3,
    "bathrooms": 2,
    "amenities": [1, 2, 3],
    "availability_date": "2025-11-01",
    "accepted_payment_methods": [1, 2],
    "zone_id": 1,
    "allows_roommates": false,
    "max_occupancy": 3,
    "min_price_per_person": "500.00",
    "is_furnished": false,
    "tenant_requirements": {"no_smoking": true},
    "tags": ["céntrico", "luminoso"],
    "semantic_embedding": null
  }
  ```
- **Campos obligatorios**:
  - `type`: Tipo de propiedad (`casa`, `departamento`, `habitacion`, `anticretico`)
  - `address`: Dirección de la propiedad
  - `latitude`: Latitud (formato decimal, hasta 10 decimales de precisión)
  - `longitude`: Longitud (formato decimal, hasta 10 decimales de precisión)
  - `price`: Precio de alquiler
- **Campos opcionales**:
  - `owner`: Se asigna automáticamente al usuario autenticado si no se especifica
  - `agent`: ID del agente (si aplica)
  - `guarantee`: Monto de garantía
  - `description`: Descripción de la propiedad
  - `size`: Tamaño en metros cuadrados
  - `bedrooms`: Número de dormitorios
  - `bathrooms`: Número de baños
  - `amenities`: Array de IDs de amenidades
  - `availability_date`: Fecha de disponibilidad
  - `accepted_payment_methods`: Array de IDs de métodos de pago aceptados
  - `zone_id`: ID de la zona (se asigna automáticamente si no se especifica)
  - `allows_roommates`: Si la propiedad permite roomies
  - `max_occupancy`: Ocupantes máximos recomendados
  - `min_price_per_person`: Precio mínimo por persona si hay roomies
  - `is_furnished`: Si está amueblada
  - `tenant_requirements`: Requisitos del inquilino (JSON)
  - `tags`: Etiquetas libres (JSON array)
  - `semantic_embedding`: Embedding semántico (opcional para IA)
- **Formato de coordenadas**:
  - **Latitud**: Debe estar entre -90 y 90 grados
  - **Longitud**: Debe estar entre -180 y 180 grados
  - **Precisión**: Hasta 9 dígitos totales con 6 decimales (ej: `-16.500000`), acorde al `PropertyCreateSerializer`
  - **Ejemplo para La Paz, Bolivia**: `latitude: "-16.500000", longitude: "-68.150000"`
- **Response (201 Created)**:
  ```json
  {
    "success": true,
    "message": "Propiedad creada exitosamente",
    "data": {
      "id": 1,
      "owner": 1,
      "agent": null,
      "type": "casa",
      "address": "Calle Falsa 123, La Paz",
      "price": "1500.00",
      "guarantee": "1500.00",
      "description": "Casa amplia en zona residencial con jardín",
      "size": 120.5,
      "bedrooms": 3,
      "bathrooms": 2,
      "amenities": [1, 2, 3],
      "availability_date": "2025-11-01",
      "is_active": true,
      "accepted_payment_methods": [1, 2],
      "zone_id": 1,
      "allows_roommates": false,
      "max_occupancy": 3,
      "min_price_per_person": "500.00",
      "is_furnished": false,
      "tenant_requirements": {"no_smoking": true},
      "tags": ["céntrico", "luminoso"],
      "semantic_embedding": null
    }
  }
  ```
 - **Ejemplo (curl)**:
   ```bash
   curl -X POST http://localhost:8000/api/properties/ \
     -H "Authorization: Bearer TU_TOKEN_JWT" \
     -H "Content-Type: application/json" \
     -d '{
       "type": "casa",
       "address": "Calle Falsa 123, La Paz",
       "latitude": "-16.500000",
       "longitude": "-68.150000",
       "price": "1500.00",
       "amenities": [1,2],
       "accepted_payment_methods": [1],
       "zone_id": 1,
       "allows_roommates": false
     }'
   ```
- **Errores comunes**:
  - **400 Bad Request** - Coordenadas con demasiados dígitos:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "latitude": ["Ensure that there are no more than 9 digits in total."],
        "longitude": ["Ensure that there are no more than 9 digits in total."]
      }
    }
    ```
  - **400 Bad Request** - Coordenadas fuera de rango:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "non_field_errors": ["La latitud debe estar entre -90 y 90."]
      }
    }
    ```
  - **400 Bad Request** - Falta de coordenadas:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "non_field_errors": ["Debe proporcionar coordenadas (latitude/longitude) o zone_id."]
      }
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "success": false,
      "message": "Token de autenticación requerido",
      "data": null
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para crear propiedades",
      "data": null
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "success": false,
      "message": "Error interno del servidor",
      "data": null
    }
    ```
 
 - **Siguiente paso recomendado**:
   - Usa el `id` retornado para subir fotos de la propiedad:
     ```bash
     curl -X POST http://localhost:8000/api/photos/ \
       -H "Authorization: Bearer TU_TOKEN_JWT" \
       -H "Content-Type: multipart/form-data" \
       -F "property=<ID_DEVUELTO_EN_CREACION>" \
       -F "image=@/ruta/a/foto.jpg" \
       -F "caption=Fachada principal"
     ```

-### `GET /api/properties/{id}/`
- **Descripción**: Obtiene los detalles de una propiedad específica.
- **Autenticación**: Opcional (lectura pública).
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Propiedad obtenida exitosamente",
    "data": {
      "id": 1,
      "type": "casa",
      "address": "Calle Falsa 123, La Paz",
      "description": "Casa amplia en zona residencial con jardín y piscina",
      "price": "1500.00",
      "bedrooms": 3,
      "bathrooms": 2,
      "size": 150.5,
      "latitude": "-16.500000",
      "longitude": "-68.150000",
      "owner": 1,
      "created_at": "2025-10-22T10:00:00Z",
      "updated_at": "2025-10-22T10:00:00Z",
      "accepted_payment_methods": [1, 2],
      "zone_id": 1,
      "zone_name": "Zona Sur"
    }
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Propiedad no encontrada",
      "data": null
    }
    ```

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
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Propiedad actualizada exitosamente",
    "data": {
      "id": 1,
      "title": "Casa en Zona Sur",
      "description": "Casa amplia en zona residencial con jardín y piscina",
      "price": "1800.00",
      "property_type": "casa",
      "bedrooms": 3,
      "bathrooms": 2,
      "area": 150.5,
      "latitude": "16.5000000000",
      "longitude": "68.1500000000",
      "owner": 1,
      "created_at": "2025-10-22T10:00:00Z",
      "updated_at": "2025-10-22T12:00:00Z",
      "accepted_payment_methods": [1, 2],
      "zone_id": 1,
      "zone_name": "Zona Sur"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "price": ["Este campo es requerido."]
      }
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para actualizar esta propiedad",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Propiedad no encontrada",
      "data": null
    }
    ```

### `DELETE /api/properties/{id}/`
- **Descripción**: Elimina una propiedad.
- **Autenticación**: Requerida (solo propietario o administrador).
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Propiedad eliminada exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para eliminar esta propiedad",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Propiedad no encontrada",
      "data": null
    }
    ```

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
    "success": true,
    "message": "Fotos obtenidas exitosamente",
    "data": {
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
 - **Ejemplo (curl)**:
   ```bash
   curl -X POST http://localhost:8000/api/photos/ \
     -H "Authorization: Bearer TU_TOKEN_JWT" \
     -H "Content-Type: multipart/form-data" \
     -F "property=1" \
     -F "image=@/ruta/a/foto.jpg" \
     -F "caption=Fachada principal"
   ```
   - `property` debe ser el ID real de una propiedad existente (no usar `0`).
   - Usa `-F` para enviar `multipart/form-data`; enviar JSON con `image` no funcionará.
   - Asegúrate de tener permisos sobre la propiedad (propietario o agente asignado).
- **Response (201 Created)**:
  ```json
  {
    "success": true,
    "message": "Foto subida exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "image": "http://localhost:8000/media/properties/foto1.jpg",
      "caption": "Fachada de la propiedad",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "property": ["Este campo es requerido."],
        "image": ["No se ha enviado ningún archivo."]
      }
    }
    ```
  - **400 Bad Request** - Propiedad inválida o inexistente:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "property": ["Invalid pk \"0\" - object does not exist."]
      }
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "success": false,
      "message": "Token de autenticación requerido",
      "data": null
    }
    ```
  - **415 Unsupported Media Type** (si no se usa `multipart/form-data`):
    ```json
    {
      "success": false,
      "message": "Error de solicitud",
      "data": {
        "detail": "Unsupported media type \"application/json\" in request."
      }
    }
    ```

### `GET /api/photos/{id}/`
- **Descripción**: Obtiene los detalles de una foto específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Foto obtenida exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "image": "http://localhost:8000/media/properties/foto1.jpg",
      "caption": "Fachada de la propiedad",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Foto no encontrada",
      "data": null
    }
    ```

### `PUT/PATCH /api/photos/{id}/`
- **Descripción**: Actualiza una foto (solo caption, no se puede cambiar la imagen).
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Request Body (PATCH)**:
  ```json
  {
    "caption": "Nueva descripción de la foto"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Foto actualizada exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "image": "http://localhost:8000/media/properties/foto1.jpg",
      "caption": "Nueva descripción de la foto",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para actualizar esta foto",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Foto no encontrada",
      "data": null
    }
    ```

### `DELETE /api/photos/{id}/`
- **Descripción**: Elimina una foto.
- **Autenticación**: Requerida (solo propietario o agente de la propiedad).
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Foto eliminada exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para eliminar esta foto",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Foto no encontrada",
      "data": null
    }
    ```

**Nota**: Las imágenes se almacenan en el directorio `media/properties/` del servidor.

## 5. Endpoints de Amenidades (`/api/amenities/`)

Gestiona las amenidades disponibles para las propiedades.

### `GET /api/amenities/`
- **Descripción**: Obtiene una lista paginada de todas las amenidades disponibles.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Amenidades obtenidas exitosamente",
    "data": {
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
    "success": true,
    "message": "Amenidad creada exitosamente",
    "data": {
      "id": 5,
      "name": "Sauna"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "name": ["Este campo es requerido."]
      }
    }
    ```

### `GET /api/amenities/{id}/`
- **Descripción**: Obtiene los detalles de una amenidad específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Amenidad obtenida exitosamente",
    "data": {
      "id": 5,
      "name": "Sauna"
    }
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Amenidad no encontrada",
      "data": null
    }
    ```

### `PUT/PATCH /api/amenities/{id}/`
- **Descripción**: Actualiza una amenidad existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "name": "Piscina Climatizada"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Amenidad actualizada exitosamente",
    "data": {
      "id": 1,
      "name": "Piscina Climatizada"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "name": ["Este campo es requerido."]
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Amenidad no encontrada",
      "data": null
    }
    ```

### `DELETE /api/amenities/{id}/`
- **Descripción**: Elimina una amenidad.
- **Autenticación**: Requerida.
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Amenidad eliminada exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Amenidad no encontrada",
      "data": null
    }
    ```

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
    "success": true,
    "message": "Garantías obtenidas exitosamente",
    "data": {
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
    "success": true,
    "message": "Garantía creada exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "tenant": 2,
      "amount": "1500.00",
      "is_released": false,
      "release_date": null,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "property": ["Este campo es requerido."],
        "tenant": ["Este campo es requerido."],
        "amount": ["Este campo es requerido."]
      }
    }
    ```

### `GET /api/guarantees/{id}/`
- **Descripción**: Obtiene los detalles de una garantía específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Garantía obtenida exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "tenant": 2,
      "amount": "1500.00",
      "is_released": false,
      "release_date": null,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Garantía no encontrada",
      "data": null
    }
    ```

### `PUT/PATCH /api/guarantees/{id}/`
- **Descripción**: Actualiza una garantía existente.
- **Autenticación**: Requerida (solo propietario o inquilino involucrado).
- **Request Body (PATCH)**:
  ```json
  {
    "amount": "1800.00"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Garantía actualizada exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "tenant": 2,
      "amount": "1800.00",
      "is_released": false,
      "release_date": null,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "amount": ["Ingrese un número válido."]
      }
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para actualizar esta garantía",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Garantía no encontrada",
      "data": null
    }
    ```

### `POST /api/guarantees/{id}/release/`
- **Descripción**: Acción personalizada que libera la garantía.
- **Autenticación**: Requerida (solo propietario).
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Garantía liberada exitosamente",
    "data": {
      "status": "guarantee released"
    }
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para liberar esta garantía",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Garantía no encontrada",
      "data": null
    }
    ```

### `DELETE /api/guarantees/{id}/`
- **Descripción**: Elimina una garantía.
- **Autenticación**: Requerida (solo propietario o admin).
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Garantía eliminada exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para eliminar esta garantía",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Garantía no encontrada",
      "data": null
    }
    ```

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
    "success": true,
    "message": "Incentivos obtenidos exitosamente",
    "data": {
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
    "success": true,
    "message": "Incentivo creado exitosamente",
    "data": {
      "id": 1,
      "user": 1,
      "amount": "500.00",
      "description": "Incentivo por referir nuevo usuario",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "user": ["Este campo es requerido."],
        "amount": ["Este campo es requerido."],
        "description": ["Este campo es requerido."]
      }
    }
    ```

### `GET /api/incentives/{id}/`
- **Descripción**: Obtiene los detalles de un incentivo específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Incentivo obtenido exitosamente",
    "data": {
      "id": 1,
      "user": 1,
      "amount": "500.00",
      "description": "Incentivo por referir nuevo usuario",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Incentivo no encontrado",
      "data": null
    }
    ```

### `PUT/PATCH /api/incentives/{id}/`
- **Descripción**: Actualiza un incentivo existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "description": "Incentivo por referir nuevo usuario - Actualizado"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Incentivo actualizado exitosamente",
    "data": {
      "id": 1,
      "user": 1,
      "amount": "500.00",
      "description": "Incentivo por referir nuevo usuario - Actualizado",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "description": ["Este campo no puede estar vacío."]
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Incentivo no encontrado",
      "data": null
    }
    ```

### `GET /api/incentives/active/`
- **Descripción**: Obtiene los incentivos activos del usuario autenticado.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Incentivos activos obtenidos exitosamente",
    "data": [
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
  }
  ```

### `GET /api/incentives/by_zone/?zone_id={zone_id}`
- **Descripción**: Obtiene los incentivos del usuario filtrados por zona específica.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `zone_id` (requerido): ID de la zona
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Incentivos por zona obtenidos exitosamente",
    "data": [
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
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Parámetro zone_id es requerido",
      "data": null
    }
    ```

### `POST /api/incentives/{id}/use/`
- **Descripción**: Marca un incentivo como usado (lo desactiva).
- **Autenticación**: Requerida (solo el propietario del incentivo).
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Incentivo usado exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para usar este incentivo",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Incentivo no encontrado",
      "data": null
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
    "success": true,
    "message": "Reglas de incentivos obtenidas exitosamente",
    "data": {
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
    "success": true,
    "message": "Incentivos generados exitosamente",
    "data": {
      "message": "Generated 5 incentives for Centro",
      "incentives_count": 5,
      "timestamp": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para generar incentivos",
      "data": null
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
    "success": true,
    "message": "Análisis de mercado obtenido exitosamente",
    "data": {
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
  }
  ```
- **Response para todas las zonas (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Análisis de mercado para todas las zonas obtenido exitosamente",
    "data": {
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
  }
  ```

### `POST /api/incentive-rules/{id}/toggle_active/`
- **Descripción**: Activa o desactiva una regla de incentivo (solo administradores).
- **Autenticación**: Requerida (solo administradores).
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Regla activada exitosamente",
    "data": {
      "message": "Rule activated successfully",
      "rule": {
        "id": 1,
        "name": "Alta Demanda",
        "is_active": true,
        "created_at": "2025-10-22T10:00:00Z"
      }
    }
  }
  ```
- **Errores comunes**:
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para modificar reglas de incentivos",
      "data": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Regla de incentivo no encontrada",
      "data": null
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
    "success": true,
    "message": "Zonas obtenidas exitosamente",
    "data": {
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
- **Response (201 Created)**:
  ```json
  {
    "success": true,
    "message": "Zona creada exitosamente",
    "data": {
      "id": 11,
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
      },
      "offer_count": 0,
      "demand_count": 0,
      "avg_price": "0.00",
      "created_at": "2025-10-22T10:00:00Z",
      "updated_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "name": ["Este campo es requerido."],
        "bounds": ["Formato de coordenadas inválido."]
      }
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "success": false,
      "message": "No tienes permisos para crear zonas",
      "data": null
    }
    ```

### `GET /api/zones/{id}/`
- **Descripción**: Obtiene detalles de una zona específica.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Zona obtenida exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Zona no encontrada",
      "data": null
    }
    ```

### `GET /api/zones/stats/`
- **Descripción**: Obtiene estadísticas agregadas de todas las zonas.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Estadísticas de zonas obtenidas exitosamente",
    "data": {
      "total_zones": 10,
      "total_properties": 150,
      "total_demand": 300,
      "avg_price_all_zones": "1150.00",
      "zones_with_high_demand": 3,
      "zones_with_low_supply": 2,
      "last_updated": "2025-10-22T12:00:00Z"
    }
  }
  ```

### `GET /api/zones/{id}/stats/`
- **Descripción**: Obtiene estadísticas detalladas de una zona específica.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Estadísticas de zona obtenidas exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Zona no encontrada",
      "data": null
    }
    ```

### `GET /api/zones/heatmap/`
- **Descripción**: Obtiene datos para generar un mapa de calor de actividad por zonas.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Datos de mapa de calor obtenidos exitosamente",
    "data": {
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
  }
  ```

### `GET /api/zones/geojson/`
- **Descripción**: Obtiene todas las zonas en formato GeoJSON para mapas.
- **Autenticación**: No requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Datos GeoJSON obtenidos exitosamente",
    "data": {
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
    "success": true,
    "message": "Búsqueda registrada exitosamente",
    "data": {
      "id": 1,
      "zone": 1,
      "search_query": "departamento 2 dormitorios",
      "user_ip": "192.168.1.1",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "zone": ["Este campo es requerido."],
        "search_query": ["Este campo es requerido."]
      }
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
    "success": true,
    "message": "Zonas cercanas obtenidas exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Zona no encontrada",
      "data": null
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
    "success": true,
    "message": "Zona encontrada exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Parámetros de ubicación requeridos",
      "data": {
        "lat": ["Este parámetro es requerido."],
        "lng": ["Este parámetro es requerido."]
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "No se encontró ninguna zona para esta ubicación",
      "data": null
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
    "success": true,
    "message": "Pagos obtenidos exitosamente",
    "data": {
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
    "success": true,
    "message": "Pago registrado exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "property": ["Este campo es requerido."],
        "amount": ["Debe ser un número válido."]
      }
    }
    ```

### `GET /api/payments/{id}/`
- **Descripción**: Obtiene los detalles de un pago específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Pago obtenido exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Pago no encontrado",
      "data": null
    }
    ```

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
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Pago actualizado exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "tenant": 2,
      "amount": "1500.00",
      "status": "pagado",
      "due_date": "2025-11-07",
      "paid_date": "2025-10-22",
      "fine": "0.00",
      "method": 1,
      "created_at": "2025-10-22T10:00:00Z",
      "updated_at": "2025-10-22T12:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "status": ["Estado inválido."]
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Pago no encontrado",
      "data": null
    }
    ```

### `DELETE /api/payments/{id}/`
- **Descripción**: Elimina un pago.
- **Autenticación**: Requerida.
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Pago eliminado exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Pago no encontrado",
      "data": null
    }
    ```

**Estados de pago disponibles:**
- `pendiente`: Pago aún no realizado
- `pagado`: Pago completado
- `retrasado`: Pago vencido sin completar

## 11. Endpoints de Métodos de Pago (`/api/payment-methods/`)

Gestiona los métodos de pago disponibles en el sistema.

### `GET /api/payment-methods/`
- **Descripción**: Obtiene una lista paginada de todos los métodos de pago.
- **Autenticación**: Requerida.
- **Parámetros de consulta**:
  - `user`: Filtra por ID del usuario (métodos personalizados)
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Métodos de pago obtenidos exitosamente",
    "data": {
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
    "success": true,
    "message": "Método de pago creado exitosamente",
    "data": {
      "id": 4,
      "name": "PayPal",
      "user": null
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "name": ["Este campo es requerido."]
      }
    }
    ```

### `GET /api/payment-methods/{id}/`
- **Descripción**: Obtiene los detalles de un método de pago específico.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Método de pago obtenido exitosamente",
    "data": {
      "id": 4,
      "name": "PayPal",
      "user": null
    }
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Método de pago no encontrado",
      "data": null
    }
    ```

### `PUT/PATCH /api/payment-methods/{id}/`
- **Descripción**: Actualiza un método de pago existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "name": "PayPal Empresarial"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Método de pago actualizado exitosamente",
    "data": {
      "id": 4,
      "name": "PayPal Empresarial",
      "user": null
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**:
    ```json
    {
      "success": false,
      "message": "Datos inválidos",
      "data": {
        "name": ["Este campo es requerido."]
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Método de pago no encontrado",
      "data": null
    }
    ```

### `DELETE /api/payment-methods/{id}/`
- **Descripción**: Elimina un método de pago.
- **Autenticación**: Requerida.
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Método de pago eliminado exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **404 Not Found**:
    ```json
    {
      "success": false,
      "message": "Método de pago no encontrado",
      "data": null
    }
    ```

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
    "success": true,
    "message": "Reseñas obtenidas exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para acceder a las reseñas
  - **500 Internal Server Error**: Error interno del servidor

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
    "success": true,
    "message": "Reseña creada exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "user": 2,
      "rating": 5,
      "comment": "Excelente propiedad, muy bien ubicada y en perfecto estado",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**: Datos de entrada inválidos
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para crear reseñas
  - **404 Not Found**: Propiedad no encontrada
  - **500 Internal Server Error**: Error interno del servidor

### `GET /api/reviews/{id}/`
- **Descripción**: Obtiene los detalles de una reseña específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Reseña obtenida exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "user": 2,
      "rating": 5,
      "comment": "Excelente propiedad, muy bien ubicada y en perfecto estado",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para acceder a esta reseña
  - **404 Not Found**: Reseña no encontrada
  - **500 Internal Server Error**: Error interno del servidor

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
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Reseña actualizada exitosamente",
    "data": {
      "id": 1,
      "property": 1,
      "user": 2,
      "rating": 4,
      "comment": "Buena propiedad, actualizo mi comentario después de vivir aquí",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**: Datos de entrada inválidos
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para actualizar esta reseña
  - **404 Not Found**: Reseña no encontrada
  - **500 Internal Server Error**: Error interno del servidor

### `DELETE /api/reviews/{id}/`
- **Descripción**: Elimina una reseña.
- **Autenticación**: Requerida (solo el autor o admin).
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Reseña eliminada exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para eliminar esta reseña
  - **404 Not Found**: Reseña no encontrada
  - **500 Internal Server Error**: Error interno del servidor

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
    "success": true,
    "message": "Notificaciones obtenidas exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para acceder a las notificaciones
  - **500 Internal Server Error**: Error interno del servidor

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
    "success": true,
    "message": "Notificación creada exitosamente",
    "data": {
      "id": 3,
      "user": 1,
      "message": "Tu pago de alquiler vence mañana",
      "is_read": false,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**: Datos de entrada inválidos
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para crear notificaciones
  - **404 Not Found**: Usuario no encontrado
  - **500 Internal Server Error**: Error interno del servidor

### `GET /api/notifications/{id}/`
- **Descripción**: Obtiene los detalles de una notificación específica.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Notificación obtenida exitosamente",
    "data": {
      "id": 3,
      "user": 1,
      "message": "Tu pago de alquiler vence mañana",
      "is_read": false,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para acceder a esta notificación
  - **404 Not Found**: Notificación no encontrada
  - **500 Internal Server Error**: Error interno del servidor

### `PUT/PATCH /api/notifications/{id}/`
- **Descripción**: Actualiza una notificación existente.
- **Autenticación**: Requerida.
- **Request Body (PATCH)**:
  ```json
  {
    "is_read": true
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Notificación actualizada exitosamente",
    "data": {
      "id": 3,
      "user": 1,
      "message": "Tu pago de alquiler vence mañana",
      "is_read": true,
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**: Datos de entrada inválidos
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para actualizar esta notificación
  - **404 Not Found**: Notificación no encontrada
  - **500 Internal Server Error**: Error interno del servidor

### `POST /api/notifications/{id}/mark_as_read/`
- **Descripción**: Acción personalizada que marca la notificación como leída.
- **Autenticación**: Requerida.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Notificación marcada como leída exitosamente",
    "data": {
      "status": "notification marked as read"
    }
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para marcar esta notificación
  - **404 Not Found**: Notificación no encontrada
  - **500 Internal Server Error**: Error interno del servidor

### `DELETE /api/notifications/{id}/`
- **Descripción**: Elimina una notificación.
- **Autenticación**: Requerida.
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Notificación eliminada exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para eliminar esta notificación
  - **404 Not Found**: Notificación no encontrada
  - **500 Internal Server Error**: Error interno del servidor

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
    "success": true,
    "message": "Mensajes obtenidos exitosamente",
    "data": {
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
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para acceder a los mensajes
  - **500 Internal Server Error**: Error interno del servidor

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
    "success": true,
    "message": "Mensaje enviado exitosamente",
    "data": {
      "id": 1,
      "sender": 1,
      "receiver": 2,
      "content": "Hola, estoy interesado en la propiedad que publicaste",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**: Datos de entrada inválidos
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para enviar mensajes
  - **404 Not Found**: Usuario destinatario no encontrado
  - **500 Internal Server Error**: Error interno del servidor

### `GET /api/messages/{id}/`
- **Descripción**: Obtiene los detalles de un mensaje específico.
- **Autenticación**: Requerida (solo remitente o destinatario).
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Mensaje obtenido exitosamente",
    "data": {
      "id": 1,
      "sender": 1,
      "receiver": 2,
      "content": "Hola, estoy interesado en la propiedad que publicaste",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para acceder a este mensaje
  - **404 Not Found**: Mensaje no encontrado
  - **500 Internal Server Error**: Error interno del servidor

### `PUT/PATCH /api/messages/{id}/`
- **Descripción**: Actualiza un mensaje existente.
- **Autenticación**: Requerida (solo el remitente).
- **Request Body (PATCH)**:
  ```json
  {
    "content": "Hola, estoy muy interesado en la propiedad que publicaste"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Mensaje actualizado exitosamente",
    "data": {
      "id": 1,
      "sender": 1,
      "receiver": 2,
      "content": "Hola, estoy muy interesado en la propiedad que publicaste",
      "created_at": "2025-10-22T10:00:00Z"
    }
  }
  ```
- **Errores comunes**:
  - **400 Bad Request**: Datos de entrada inválidos
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para actualizar este mensaje
  - **404 Not Found**: Mensaje no encontrado
  - **500 Internal Server Error**: Error interno del servidor

### `DELETE /api/messages/{id}/`
- **Descripción**: Elimina un mensaje.
- **Autenticación**: Requerida (solo el remitente o admin).
- **Response (204 No Content)**:
  ```json
  {
    "success": true,
    "message": "Mensaje eliminado exitosamente",
    "data": null
  }
  ```
- **Errores comunes**:
  - **401 Unauthorized**: Token de autenticación inválido o faltante
  - **403 Forbidden**: Sin permisos para eliminar este mensaje
  - **404 Not Found**: Mensaje no encontrado
  - **500 Internal Server Error**: Error interno del servidor

**Consejos para obtener conversaciones:**
- Para obtener mensajes entre dos usuarios específicos, usa: `/api/messages/?sender=1&receiver=2` y `/api/messages/?sender=2&receiver=1`
- Ordena por `created_at` para mostrar cronológicamente

## 7. Endpoints de Matching (`/api/search_profiles/`, `/api/roommate_requests/`, `/api/matches/`, `/api/match_feedback/`, `/api/recommendations/`)

Sistema de matching inteligente para inquilinos, propietarios y agentes.

### `POST /api/search_profiles/`
- **Descripción**: Crea/actualiza el `SearchProfile` del usuario autenticado con preferencias de búsqueda.
- **Autenticación**: Requerida.
- **Request Body (JSON)**:
  - `latitude`/`longitude` (opcional): Coordenadas base del perfil, se convierten a `Point`
  - `budget_min`, `budget_max` (opcional): Presupuesto
  - `desired_types` (opcional): Array de tipos deseados
  - `bedrooms_min`, `bedrooms_max` (opcional)
  - `amenities` (opcional): IDs de amenidades
  - `roommate_preference` (opcional): `no` | `looking` | `open`
  - `roommate_preferences`, `vibes` (opcional): JSON/array libre
  - `preferred_zones` (opcional): Array de IDs de zonas preferidas
  - Campos adicionales para mejorar el matching:
    - `age` (opcional): Edad
    - `children_count` (opcional): Número de hijos
    - `family_size` (opcional): Tamaño del grupo familiar
    - `smoker` (opcional): Si fuma
    - `gender` (opcional): `male` | `female` | `other`
    - `occupation` (opcional): Ocupación (texto)
    - `has_vehicle` (opcional): Si tiene vehículo
    - `commute_distance_km` (opcional): Distancia de traslado preferida
    - `education_level` (opcional): Nivel educativo (texto)
    - `pets_count` (opcional): Número de mascotas
    - `languages` (opcional): Array de idiomas
    - `lifestyle` (opcional): JSON libre con estilo de vida
    - `schedule` (opcional): JSON libre con horarios
- **Response (200/201)**: Perfil creado/actualizado.

### `GET /api/search_profiles/my/`
- **Descripción**: Obtiene el `SearchProfile` del usuario autenticado.
- **Autenticación**: Requerida.

### `POST /api/roommate_requests/`
- **Descripción**: Crea una solicitud de roommate asociada al `SearchProfile`.
- **Autenticación**: Requerida.
- **Request Body**: `desired_move_in_date`, `max_roommates`, `gender_preference`, `smoker_ok`, `budget_per_person`.

### `GET /api/roommate_requests/my/`
- **Descripción**: Lista las solicitudes de roommate creadas por el usuario autenticado.
- **Autenticación**: Requerida.

### `GET /api/search_profiles/{id}/matches/?type=property|roommate|agent`
- **Descripción**: Lista matches paginados asociados al perfil de búsqueda indicado, ordenados por score.
- **Autenticación**: Requerida.
- **Query params**:
  - `type`: `property` (por defecto) | `roommate` | `agent`
  - `status` (opcional): `pending` | `accepted` | `rejected` para filtrar por estado
- **Response (200 OK)**: Respuesta paginada estándar de DRF (`count`, `next`, `previous`, `results`).
- **Acciones relacionadas**:
  - `POST /api/matches/{id}/accept/`: Acepta un match y crea notificación/mensaje.
  - `POST /api/matches/{id}/reject/`: Rechaza un match y almacena feedback opcional.

### `POST /api/match_feedback/`
- **Descripción**: Envía feedback sobre un match (`like`, `dislike`, `neutral`) con razón opcional.
- **Autenticación**: Requerida.
 - **Request Body (JSON)**:
   - `match`: ID del match
   - `user`: ID del usuario (se valida que sea el autenticado)
   - `feedback_type`: `like` | `dislike` | `neutral`
   - `reason` (opcional): Texto con la razón del feedback

### `GET /api/recommendations/?type=mixed|property|roommate|agent`
- **Descripción**: Obtiene recomendaciones híbridas para el `SearchProfile` del usuario. Genera matches on-demand antes de listar.
- **Autenticación**: Requerida.
- **Notas**: `type=mixed` incluye resultados de propiedades, roomies y agentes; se devuelve un arreglo con elementos `{type, match}`.

- **Ejemplo (type=property)**
  ```http
  GET /api/recommendations/?type=property
  Authorization: Bearer <token>
  ```
  ```json
  {
    "results": [
      {
        "type": "property",
        "match": {
          "id": 123,
          "match_type": "property",
          "subject_id": 45,          // ID de la Property
          "target_user": 7,          // ID del usuario actual
          "score": 85.2,
          "status": "pending",
          "metadata": { "details": { /* explicación del score */ } },
          "created_at": "2025-11-05T12:00:00Z",
          "updated_at": "2025-11-05T12:00:00Z"
        }
      }
    ]
  }
  ```

- **Ejemplo (type=roommate)**
  ```http
  GET /api/recommendations/?type=roommate
  Authorization: Bearer <token>
  ```
  ```json
  {
    "results": [
      {
        "type": "roommate",
        "match": {
          "id": 456,
          "match_type": "roommate",
          "subject_id": 12,          // ID del SearchProfile del otro usuario
          "target_user": 7,
          "score": 80.0,
          "status": "pending",
          "metadata": { "details": { /* explicación del score */ } },
          "created_at": "2025-11-05T12:00:00Z",
          "updated_at": "2025-11-05T12:00:00Z"
        }
      }
    ]
  }
  ```

### Flujo de "Like" y almacenamiento
- Al listar matches, el usuario puede enviar un "like" a través de `POST /api/matches/{id}/accept/`.
- Al aceptar:
  - Se actualiza el `status` del `Match` a `accepted`.
  - Se envía una `Notification` al usuario confirmando el like.
  - Si el match es de tipo `property`, se crea un `Message` automático al propietario: "Hola, me interesa tu propiedad (match X%)".
  - Además, se envía una `Notification` al propietario indicando: "<usuario> está interesado en tu propiedad (match X%)".
- El historial de likes puede consultarse listando `GET /api/search_profiles/{id}/matches/?status=accepted`.

### Cómo se eligen las propiedades mostradas
- El sistema genera matches con `score` calculado por reglas: ubicación, precio vs presupuesto, amenities, preferencias de roomie, reputación y frescura, y un factor familiar (p.ej., hijos vs dormitorios).
- Solo se almacenan matches con `score >= 70`.
- Para listar propiedades directamente: `GET /api/properties/?match_score=70` filtra según el `SearchProfile` del usuario autenticado.
- Para una experiencia tipo swipe y priorizar probabilidades altas, usa `GET /api/search_profiles/{id}/matches/?type=property`.
 - El matching para roomies considera el solapamiento de `preferred_zones` entre perfiles.

### Notas de Matching
- Al crear una `Property`, el sistema genera matches automáticos con perfiles existentes si el score >= 70.
- El listado de propiedades soporta `match_score` para filtrar en base al perfil del usuario.
- `Zone` expone métricas nuevas en `zone_stats`: `match_ratio` y `roomie_demand`.

## 8. Endpoints de Zonas (`/api/zones/`) – Métricas de Matching

### `GET /api/zones/{id}/stats/`
- **Descripción**: Incluye métricas adicionales:
  - `match_ratio`: proporción de matches aceptados / matches totales para propiedades de la zona.
  - `roomie_demand`: cantidad de solicitudes de roommate activas con preferencia por la zona.


