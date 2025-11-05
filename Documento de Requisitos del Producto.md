# Documento de Requisitos del Producto (PRD)

## Visión y Objetivo
La plataforma Habitto centraliza el ciclo completo de búsqueda, publicación y gestión de propiedades de alquiler, integrando perfiles de usuario, matching inteligente (propiedades, roomies y agentes), mensajería, pagos, garantías, reseñas, zonas y notificaciones. Este PRD unifica funcionalidades, flujos, endpoints y modelos de datos para asegurar coherencia entre equipos de producto, diseño y desarrollo.

---

## Alcance
- Usuarios y Perfiles (registro, perfil, verificación, foto e historial, favoritos).
- Propiedades (CRUD, búsqueda avanzada, mapa, GeoJSON, cercanas, estadísticas).
- Zonas (listado, estadísticas, heatmap/geojson, cercanas, señales de actualización).
- Amenidades y Métodos de Pago (CRUD básico, uso en filtros y relaciones).
- Fotos (subida y asociación a propiedades).
- Garantías (creación y liberación).
- Pagos (creación y consulta) y Métodos de Pago.
- Mensajes (comunicación entre usuarios, p.ej. interesado ↔ propietario).
- Notificaciones (eventos del sistema, marcar como leído).
- Matching (perfiles de búsqueda, matches, aceptación/rechazo, recomendaciones, feedback).
- Autenticación y estandarización de respuestas API.

---

## Roles de Usuario
- Inquilino: busca propiedades, crea perfil de búsqueda, recibe recomendaciones, envía mensajes, realiza pagos, deja reseñas.
- Propietario: publica propiedades, recibe interés y mensajes, ve estadísticas de sus zonas/propiedades.
- Agente: puede actuar como facilitador; tiene campos específicos (comisiones) y puede ser parte del matching.
- Administrador: superusuario con control sobre CRUD y moderación en todo el sistema.

---

## Reglas de Negocio Clave
- Registro público permitido; acciones posteriores requieren autenticación.
- Al crear propiedad, se asigna automáticamente el `owner` y se disparan cálculos de matches para perfiles cercanos con presupuesto compatible.
- Aceptar un Match genera notificaciones y mensajes entre partes involucradas.
- La actualización de una foto de perfil crea historial y marca la nueva foto como actual; las anteriores se marcan como no actuales.
- Zonas mantienen estadísticas agregadas vía señales cuando cambian propiedades o favoritos.

---

## Modelos de Datos (Resumen)

### Usuario y Perfil (`user.models`)
- `User` (Django): `username`, `email`, `first_name`, `last_name`, `date_joined`.
- `UserProfile`:
  - `user` (OneToOne con `User`), `user_type` (`inquilino`|`propietario`|`agente`).
  - `phone`, `profile_picture` (ruta única `profile_pictures/user_<id>_<timestamp>_<uuid>.<ext>`), `is_verified`.
  - `favorites` (ManyToMany a `property.Property`).
  - Campos agent/roomie: `is_agent` (bool), `agent_commission_rate` (decimal), `roommate_vibes` (JSON).
  - Tiempos: `created_at`, `updated_at`.
- `ProfilePictureHistory`:
  - `user_profile` (FK), `image`, `original_filename`, `uploaded_at`, `is_current` (bool), `ordering` por `uploaded_at` desc.

### Matching (`matching.models`)
- `SearchProfile`:
  - Ubicación: `location` (Point, SRID 4326).
  - Presupuesto: `budget_min`, `budget_max`.
  - Preferencias: `desired_types`, `bedrooms_min/max`, `pet_allowed`, `wfh_preference`.
  - Roomies: `roommate_preference` (`no`|`looking`|`open`), `roommate_preferences` (JSON), `vibes` (list).
  - Atributos personales: `age`, `gender`, `family_size`, `children_count`, `has_vehicle`, `commute_distance_km`, `occupation`, `education_level`, `pets_count`, `languages` (list), `lifestyle` (dict), `schedule` (dict), `smoker`.
  - `semantic_embedding` (texto), `created_at`, `updated_at`.
  - Relaciones: `amenities` (ManyToMany a `amenity.Amenity`).
- `Match`:
  - `match_type` (`property`|`roommate`|`agent`), `subject_id` (ID del recurso sujeto), `target_user` (FK a User), `score`, `metadata` (JSON), `status` (`pending`|`accepted`|`rejected`), timestamps.
  - Índices en `match_type/target_user`, `match_type/subject_id`, `status`.
- `MatchFeedback`:
  - `match` (FK), `user` (FK), `feedback_type` (`like`|`dislike`|`neutral`), `reason` (opcional), `created_at`.

### Propiedad (resumen basado en vistas/tests)
- Campos típicos: `owner` (User), `type`, `address`, `location` (Point), `price`, `description`, `bedrooms`, `bathrooms`, `allows_roommates`, `is_active`.
- Relaciones: amenidades (`ManyToMany`), métodos de pago disponibles.

### Zonas
- Agregan estadísticas y exponen endpoints de `stats`, `heatmap`, `geojson`, `nearby_zones` (ver Sección Endpoints).
- Señales (`zone/signals.py`) actualizan métricas al cambiar propiedades y favoritos.

### Amenidades (`amenity.models`)
- `Amenity`: `name`.

### Métodos de Pago (`paymentmethod.models`)
- `PaymentMethod`: `name`, `user` (FK opcional).

### Pagos
- `Payment`: creación y consulta; se integra con propiedades/métodos.

### Garantías (`guarantee`)
- `Guarantee`: acciones como `release`.

### Fotos
- `Photo`: imagen, relación a `Property`.

### Notificaciones (`notification`)
- `Notification`: `user`, `message`, `is_read` (marcar como leído), timestamps.

### Mensajes (`message`)
- `Message`: `sender`, `receiver`, `content`, relación opcional a `Property/Match`, timestamps.

---

## Flujos Principales

### Registro y Autenticación
- Registro público (`UserViewSet.create`): crea `User` y automáticamente `UserProfile`, acepta `user_type`, `phone` y `profile_picture` (opcional). Si hay imagen, se registra en `ProfilePictureHistory`.
- Autenticación JWT: `/api/login/`, `/api/refresh/`.
- Protección general: resto de acciones requieren autenticación (`IsAuthenticated`).

### Gestión de Perfil
- Ver usuario actual: `GET /api/users/me/`.
- Ver/editar perfil actual: `GET /api/profiles/me/`, `PUT/PATCH /api/profiles/update_me/`.
- Subir foto de perfil: `POST /api/profiles/upload_profile_picture/` con `profile_picture` en `FILES`. Actualiza `UserProfile.profile_picture`, marca historial (`is_current=true`), desactiva anteriores.
- Historial de fotos: `GET /api/profiles/picture_history/`.
- Verificación: `POST /api/profiles/{id}/verify/`.
- Favoritos: manejar vía `UserProfile.favorites` (endpoints de perfil para añadir/quitar en actualizaciones).

### Propiedades
- CRUD estándar: `/api/properties/`.
- Búsqueda avanzada: `POST /api/properties/search/` con filtros: `zone_id`, `type`, `min_price`, `max_price`, `bedrooms`, `bathrooms`, `latitude`, `longitude`, `radius_km`, `is_active`, texto libre.
- Mapa optimizado: `GET /api/properties/map/` con filtros `zone`, `location`, `radius_km`, `price`.
- Cercanas: `GET /api/properties/{id}/nearby/`.
- GeoJSON: `GET /api/properties/geojson/` (colección georreferenciada en formato GeoJSON).
- Estadísticas: `GET /api/properties/stats/` (total, activas, precio medio, desgloses por zona y personalización por tipo de usuario).
- Notas de negocio: al crear (`perform_create`), se asigna `owner`=usuario autenticado y se disparan cálculos de matching.

### Zonas
- CRUD estándar: `/api/zones/`.
- Estadísticas globales: `GET /api/zones/stats/` y `GET /api/zones/zone_stats/` (personalizadas por tipo de usuario, incluyen demanda de match/roomie).
- Heatmap/GeoJSON: `GET /api/zones/heatmap/`, `GET /api/zones/geojson/`.
- Cercanas: `GET /api/zones/nearby_zones/`.
- Señales: actualizan estadísticas cuando cambian propiedades o favoritos.

### Amenidades
- CRUD: `/api/amenities/`.

### Métodos de Pago
- CRUD: `/api/payment-methods/` (de usuario o globales).

### Pagos
- CRUD: `/api/payments/`.

### Garantías
- CRUD: `/api/guarantees/`.
- Liberación: `POST /api/guarantees/{id}/release/`.

### Fotos
- CRUD: `/api/photos/` (incluye subida y asociación a propiedades).

### Reseñas
- CRUD: `/api/reviews/` (deja reseñas sobre propiedades/usuarios según diseño).

### Mensajes
- CRUD: `/api/messages/`.
- Casos de uso: al aceptar match se crea un hilo de interés entre inquilino y propietario.

### Notificaciones
- CRUD: `/api/notifications/`.
- Acción: `POST /api/notifications/{id}/mark_as_read/`.

### Matching y Recomendaciones
- Perfiles de búsqueda: `GET/POST /api/search_profiles/`, `GET /api/search_profiles/{id}/matches/`.
- Matches: `GET/POST /api/matches/`, `POST /api/matches/{id}/accept/`, `POST /api/matches/{id}/reject/`.
- Recomendaciones: `GET /api/recommendations/?type=mixed|property|roommate`.
- Feedback: `POST /api/match_feedback/`.
- Tarea asíncrona (Celery): `compute_matches_for_profile(profile_id)` llama utilidades para generar matches de propiedades, roomies y agentes.

---

## Parámetros y Validaciones Clave
- `PropertySearchSerializer`: valida filtros avanzados y normaliza criterios (precio, tipos, dormitorios, baños, radio geográfico, estado).
- `PropertyMapSerializer`: optimiza payload para rendering en mapa.
- `PropertyCreateSerializer`: acepta `latitude/longitude` y asigna zona automáticamente; valida mínimos.
- `UserCreateSerializer`: valida credenciales y datos de perfil; maneja imagen de perfil y crea historial si aplica.

---

## Respuestas API Estandarizadas
- `WrappedJSONRenderer` estandariza: `{ success: bool, message: str|None, data: any }`.
- Beneficios: consistencia, manejo de errores, claridad en clientes.

---

## Permisos y Seguridad
- Registro (`users.create`): `AllowAny`.
- Resto de acciones: `IsAuthenticated`.
- Endpoints de perfil tipo `me`, `update_me`, `upload_profile_picture`, `picture_history`: autenticados.
- Endpoints de matching y acciones (`accept`, `reject`): autenticados.
- Datos sensibles (ubicación, presupuesto): uso responsable y con consentimiento.

---

## Rendimiento y Escalabilidad
- Consultas geoespaciales: uso de `Point` SRID 4326 y filtros por radio para `map`, `nearby`, `search`.
- Serializadores optimizados para mapa y búsquedas.
- Señales de zona para mantener estadísticas agregadas sin cargar endpoints.
- Tareas asíncronas (Celery) para matching masivo.

---

## Métricas y Analítica
- Conversión: creación de perfiles de búsqueda vs. creación de propiedades.
- Engagement: número de matches listados/aceptados, mensajes enviados, reseñas.
- Liquidez: tiempo desde publicación de propiedad hasta aceptación de match.
- Calidad: `score` medio de match, feedback (`like/dislike`), demanda por zona.
- Zonas: propiedades activas, precio medio, favoritos, heatmap.

---

## Experiencias de Usuario (Flujos Resumidos)
- Inquilino: registro → completa perfil → crea perfil de búsqueda → recibe recomendaciones → acepta match → envía mensaje → realiza pago → deja reseña.
- Propietario: registro → publica propiedad → consulta mapa/estadísticas → recibe interés via notificaciones/mensajes → negocia → confirma pagos/garantías.
- Agente: similar a propietario pero con KPIs y comisiones.

---

## Casos de Error y Mensajes
- Perfil inexistente en `me/update_me/upload_profile_picture/picture_history`: 404 con `detail` claro.
- Imagen faltante en upload: 400 con `detail`.
- Validaciones de búsqueda: 400 con errores de campo.

---

## Endpoints API (Inventario)
Base: `/api/`

- Autenticación: `POST /api/login/`, `POST /api/refresh/`.
- Usuarios: `GET/POST /api/users/`, `GET /api/users/{id}/`, `GET /api/users/me/`.
- Perfiles: `GET/POST /api/profiles/`, `GET /api/profiles/{id}/`, `GET /api/profiles/me/`, `PUT/PATCH /api/profiles/update_me/`, `POST /api/profiles/upload_profile_picture/`, `GET /api/profiles/picture_history/`, `POST /api/profiles/{id}/verify/`.
- Propiedades: `GET/POST /api/properties/`, `GET/PUT/PATCH/DELETE /api/properties/{id}/`, `GET /api/properties/map/`, `GET /api/properties/geojson/`, `POST /api/properties/search/`, `GET /api/properties/stats/`, `GET /api/properties/{id}/nearby/`.
- Zonas: `GET/POST /api/zones/`, `GET /api/zones/stats/`, `GET /api/zones/zone_stats/`, `GET /api/zones/heatmap/`, `GET /api/zones/geojson/`, `GET /api/zones/nearby_zones/`.
- Amenidades: `GET/POST /api/amenities/`, `GET/PUT/PATCH/DELETE /api/amenities/{id}/`.
- Fotos: `GET/POST /api/photos/`, `GET/PUT/PATCH/DELETE /api/photos/{id}/`.
- Reseñas: `GET/POST /api/reviews/`, `GET/PUT/PATCH/DELETE /api/reviews/{id}/`.
- Pagos: `GET/POST /api/payments/`, `GET/PUT/PATCH/DELETE /api/payments/{id}/`.
- Métodos de pago: `GET/POST /api/payment-methods/`, `GET/PUT/PATCH/DELETE /api/payment-methods/{id}/`.
- Garantías: `GET/POST /api/guarantees/`, `GET/PUT/PATCH/DELETE /api/guarantees/{id}/`, `POST /api/guarantees/{id}/release/`.
- Notificaciones: `GET/POST /api/notifications/`, `GET/PUT/PATCH/DELETE /api/notifications/{id}/`, `POST /api/notifications/{id}/mark_as_read/`.
- Mensajes: `GET/POST /api/messages/`, `GET/PUT/PATCH/DELETE /api/messages/{id}/`.
- Matching:
  - Perfiles de búsqueda: `GET/POST /api/search_profiles/`, `GET /api/search_profiles/{id}/`, `GET /api/search_profiles/{id}/matches/`.
  - Matches: `GET/POST /api/matches/`, `GET /api/matches/{id}/`, `POST /api/matches/{id}/accept/`, `POST /api/matches/{id}/reject/`.
  - Feedback: `POST /api/match_feedback/`.
  - Recomendaciones: `GET /api/recommendations/?type=mixed|property|roommate`.

---

## Pruebas y Cobertura
- `integration_tests/test_api_integration.py`: cubre creación de propiedad, subida de foto, mensajería, garantía (creación/liberación), pago, filtros de propiedad y autenticación.
- `property/test_api.py`: CRUD, filtros, búsqueda, mapa, cercanas y stats.
- `amenity/test_api.py`, `paymentmethod/test_api.py`: CRUD y permisos.
- `matching/test_api.py`: creación de perfiles, generación de matches, aceptación (notificaciones y mensajes), recomendaciones y feedback.

---

## Roadmap (Sugerencias)
- Moderación y verificación avanzada de perfiles/agentes.
- Scoring mejorado con embeddings semánticos (ya referenciados en modelo).
- Alertas en tiempo real (WebSockets) para matches y mensajes.
- Pagos con pasarela externa y conciliación.
- Paneles de analítica para propietarios y agentes.

---

## Anexos
- Renderizador JSON: `bk_habitto/renderers.py`.
- Configuración de apps: `bk_habitto/settings.py` (`INSTALLED_APPS` incluye `habittoapp`, `user`, `property`, `zone`, `amenity`, `photo`, `review`, `payment`, `paymentmethod`, `notification`, `message`, `incentive`, `guarantee`, `matching`).

---

## Lógica y Flujo de la App (Explicación detallada)

### Visión General
- La app se basa en tres pilares: catálogo de propiedades, perfiles de búsqueda y un motor de matching/recomendaciones que prioriza resultados por similitud y probabilidad de interés.
- Todo el ciclo (crear perfil → listar/buscar → recomendar/matchear → aceptar → mensajear/pagar) está estandarizado con respuestas `{ success, message, data }`.

### Listado de Propiedades: “por cosas parecidas o por probabilidad”
- Entrada del listado:
  - Con perfil: si el usuario tiene `SearchProfile`, el listado se reordena y/o filtra usando `match_score` (compatibilidad).
  - Sin perfil: se usan heurísticas por defecto (recientes/activas, precio medio de zona, popularidad) y filtros básicos (`type`, `price`, `is_active`, etc.).
- Generación de candidatos:
  - Se parte de propiedades `is_active=true` y que cumplan los filtros explícitos (tipo, precio, dormitorios/baños, zona si aplica).
  - En vistas geoespaciales (`map`, `nearby`) se usan coordenadas WGS84 (SRID 4326) y radio en km.
- Cálculo de similitud (con perfil):
  - Distancia geográfica entre `SearchProfile.location` y `Property.location` (más cerca, mayor score).
  - Presupuesto: penalización si `price` queda fuera de `[budget_min, budget_max]`.
  - Tipo deseado: bonus si `property.type` ∈ `desired_types`.
  - Comodidades: intersección con `amenities` del perfil y/o preferidas.
  - Capacidad: `bedrooms/bathrooms` comparado con `bedrooms_min/max` del perfil.
- Probabilidad de interés (concepto):
  - El `match_score` puede mapearse a una probabilidad usando una función logística (calibración básica) y señales de interacción (feedback `like/dislike`, aceptación de matches previos).
  - Resultado: ranking final por una combinación de similitud (contenido) + probabilidad (comportamiento), con paginación.

### Lógica de Matching
- Disparadores de match:
  - Al crear una propiedad (`perform_create`), se computan matches para perfiles cercanos y compatibles en presupuesto/tipo.
  - Tarea asíncrona `compute_matches_for_profile(profile_id)` puede recalcular matches masivos (propiedad, roomie, agente).
- Criterios principales (propiedades):
  - Distancia, presupuesto, tipo, estado (`is_active`), atributos básicos (`bedrooms`, `bathrooms`).
- Criterios principales (roommates):
  - Compatibilidad de presupuestos y ubicación.
  - Preferencia de roomie (`roommate_preference`), `vibes` y `roommate_vibes` del perfil.
  - Señales de convivencia (`lifestyle`, `schedule`, `pets_count`, `smoker`).
- Criterios principales (agentes):
  - Si `is_agent=true`, se pondera visibilidad para casos donde el usuario busca apoyo de agente (criterios de negocio/roadmap).
- Estados y acciones:
  - `Match.status`: `pending` → `accepted` o `rejected`.
  - `POST /api/matches/{id}/accept/`: cambia a `accepted`, crea notificaciones a ambas partes y un `Message` de interés.
  - `POST /api/matches/{id}/reject/`: cambia a `rejected` (puede registrar notificación). 

### Recomendaciones
- `GET /api/recommendations/?type=mixed|property|roommate`:
  - `mixed`: mezcla propiedades y roomies con mejor score para el perfil.
  - `property`: sólo propiedades compatibles y cercanas.
  - `roommate`: sólo personas/perfiles compatibles.
- Cada item incluye `type` y un objeto `match` cuando existe una correlación explícita.

### Notificaciones y Mensajes
- Aceptar un match genera:
  - Notificación al inquilino confirmando aceptación.
  - Notificación al propietario indicando interés.
  - Mensaje inicial entre ambas partes para iniciar conversación.
- `mark_as_read` permite a los usuarios gestionar su bandeja.

### Estadísticas y Señales
- Zonas: `stats/zone_stats` agregan métricas de propiedades activas, precio medio, favoritos y demanda de match/roomie.
- Señales (`zone/signals.py`) actualizan estas métricas cuando cambian propiedades o favoritos.
- Propiedades: `stats` personales por tipo de usuario (propietario/inquilino) para ayudar decisiones.

### Flujo de punta a punta (ejemplo)
- Inquilino crea `SearchProfile` con ubicación y presupuesto.
- En la vista de listado:
  - Se filtran candidatos activos según criterios explícitos.
  - Se calcula `match_score` y/o probabilidad para cada candidato.
  - Se ordena por score y se pagina.
- Inquilino revisa recomendaciones (`/recommendations/`) y/o acepta un match (`/matches/{id}/accept/`).
- El sistema crea notificaciones y un mensaje al propietario.
- Avanza a pagos/garantías según acuerdo; al finalizar contrato, se puede dejar `Review`.

### Nota sobre ordenación y experiencia
- Donde sea pertinente, el listado se puede ordenar por `match_score`, `price`, o `-created_at`.
- El mapa (`/properties/map/`) devuelve payload optimizado para rendimiento en cliente.
- La búsqueda avanzada (`/properties/search/`) es el lugar para consultas complejas; el listado básico prioriza velocidad y relevancia.

---

## Perfil vs Usuario: Relación y uso en la app

### ¿Qué es `User`?
- Es el modelo de autenticación estándar de Django. Contiene credenciales e identidad básica: `username`, `email`, `first_name`, `last_name`, `date_joined` y la contraseña (almacenada de forma segura).
- Endpoints relevantes: `POST /api/users/` (registro), `GET /api/users/me/` (usuario autenticado), `GET/PUT/PATCH/DELETE /api/users/{id}/`.

### ¿Qué es `UserProfile`?
- Es una extensión del usuario para la lógica de negocio de Habitto. Modela el “perfil” con información y preferencias adicionales:
  - `user_type` (`inquilino`|`propietario`|`agente`), `phone`, `profile_picture`, `is_verified`.
  - `favorites` (relación ManyToMany con `property.Property`) para guardar propiedades favoritas.
  - Campos específicos: `is_agent`, `agent_commission_rate`, `roommate_vibes` (usados para escenarios de agentes/roomies).
- La relación con `User` es OneToOne: en código se accede como `user.profile` (por `related_name='profile'`).

### ¿Cómo se crea y se vincula?
- Durante el registro (`POST /api/users/`), el `UserCreateSerializer` crea automáticamente el `User` y luego su `UserProfile`, tomando `user_type`, `phone` y `profile_picture` del payload.
- Si se sube una `profile_picture`, se registra también en `ProfilePictureHistory` y se marca como `is_current=true`.
- Si por algún motivo se crea el perfil manualmente, la vista `UserProfileViewSet.perform_create` asegura que se vincule al `request.user` autenticado.

### ¿Qué endpoints usan el perfil?
- `GET /api/profiles/me/`: obtiene el `UserProfile` del usuario autenticado.
- `PUT/PATCH /api/profiles/update_me/`: actualiza campos del perfil (no las credenciales de `User`).
- `POST /api/profiles/upload_profile_picture/`: actualiza la foto y crea una nueva entrada en `ProfilePictureHistory` marcando anteriores como no actuales.
- `GET /api/profiles/picture_history/`: lista el historial de fotos del perfil.
- `POST /api/profiles/{id}/verify/`: marca el perfil como verificado (`is_verified=true`).

### ¿Cómo se usa en matching y listados?
- `UserProfile` guarda la identidad y preferencias generales del usuario (p.ej. tipo de usuario, foto, favoritos). 
- El matching usa principalmente `SearchProfile` (del módulo `matching`), que es distinto a `UserProfile`:
  - `SearchProfile` contiene la ubicación (`location`), presupuestos (`budget_min/max`) y preferencias de búsqueda (`desired_types`, `bedrooms_min/max`, `amenities`, etc.).
  - El motor de recomendaciones y el `match_score` se basan en `SearchProfile` + datos de propiedades.
- En listados:
  - Si existe `SearchProfile`, se priorizan candidatos según compatibilidad; los favoritos (`UserProfile.favorites`) complementan la experiencia (p.ej. destacar ítems guardados).

### Acceso típico en código
- Obtener perfil del usuario autenticado: `profile = UserProfile.objects.get(user=request.user)`.
- Leer tipo de usuario: `request.user.profile.user_type`.
- Añadir/Quitar favoritos vía `profile.favorites.add(property_obj)` / `profile.favorites.remove(property_obj)`.

### Ejemplos de respuestas
- Usuario (`GET /api/users/me/`):
```
{
  "id": 7,
  "username": "juan",
  "email": "juan@example.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "date_joined": "2025-11-05T15:00:00Z"
}
```

- Perfil (`GET /api/profiles/me/`):
```
{
  "id": 12,
  "user": { /* usuario serializado como arriba */ },
  "user_type": "inquilino",
  "phone": "77777777",
  "profile_picture": "https://.../media/profile_pictures/user_7_20251105_abc123.jpg",
  "is_verified": false,
  "favorites": [23, 41],
  "picture_history": [
    { "id": 3, "image": "...", "original_filename": "perfil.png", "uploaded_at": "2025-11-05T15:10:00Z", "is_current": true }
  ],
  "created_at": "2025-11-05T15:00:00Z",
  "updated_at": "2025-11-05T15:10:00Z"
}
```


---

## Expectativas del Producto
- Respuestas consistentes: todas las APIs deben usar el envoltorio `{ success, message, data }`.
- Paginación estándar: endpoints de listado deben retornar `count`, `next`, `previous`, `results` cuando aplique. Parámetro `?page=` disponible.
- Filtros claros: 
  - Listado básico: query params (`type`, `price`, `is_active`, etc.).
  - Búsqueda avanzada: cuerpo (`POST /properties/search/`).
  - Mapa: query params optimizados (`/properties/map/`).
- Ordenación: usar `?ordering=` cuando esté habilitado (p.ej. `price`, `-created_at`).
- Mensajería y notificaciones: acciones de aceptación/rechazo deben generar eventos visibles al usuario.
- Semántica geoespacial: coordenadas en WGS84 (SRID 4326), radios en kilómetros.
- Idioma: mensajes de usuario en español; claves y contratos de API en inglés/español según contexto.

---

## Criterios de Aceptación por Módulo

### Usuarios y Perfiles
- Registro crea `User` y `UserProfile` automáticamente; retorna usuario serializado sin contraseña.
- `GET /api/users/me/` retorna el usuario autenticado con `id`, `username`, `email`, nombres.
- `GET /api/profiles/me/` retorna perfil si existe; si no, 404 con `detail` claro.
- `PUT/PATCH /api/profiles/update_me/` permite actualización parcial y mantiene historial si cambia `profile_picture`.
- `POST /api/profiles/upload_profile_picture/` requiere `profile_picture` en `FILES`; marca anterior como `is_current=false` y nueva en historial.
- `GET /api/profiles/picture_history/` retorna lista ordenada desc por `uploaded_at`.
- `POST /api/profiles/{id}/verify/` marca `is_verified=true` y responde `{ status: 'verified' }`.

### Propiedades
- Crear propiedad asigna `owner` al usuario autenticado y dispara creación de matches relevantes.
- `POST /api/properties/search/` filtra por todos los criterios soportados y retorna únicamente propiedades que cumplan.
- `GET /api/properties/map/` retorna payload optimizado (campos mínimos para mapa) y respeta filtros geográficos.
- `GET /api/properties/{id}/nearby/` devuelve propiedades dentro del radio solicitado.
- `GET /api/properties/geojson/` retorna `FeatureCollection` válida.
- `GET /api/properties/stats/` incluye totales, activas, precio medio y desgloses por zona; se personaliza por tipo de usuario.

### Matching y Recomendaciones
- Al crear propiedad compatible, se generan `Match` para perfiles cercanos con presupuesto alineado.
- `GET /api/search_profiles/{id}/matches/` lista matches del perfil con paginación.
- `POST /api/matches/{id}/accept/` cambia estado a `accepted`, crea notificación al inquilino y propietario y un mensaje de interés.
- `POST /api/matches/{id}/reject/` cambia estado a `rejected` y puede generar notificación según configuración.
- `GET /api/recommendations/?type=...` retorna lista con `type` (`property`|`roommate`) y objeto `match` asociado.
- `POST /api/match_feedback/` persiste feedback y asocia al `Match` y `User`.

### Mensajes y Notificaciones
- `POST /api/notifications/{id}/mark_as_read/` cambia `is_read=true` y retorna estado actualizado.
- Aceptación de match crea `Message` entre inquilino y propietario.
- Listados de mensajes y notificaciones soportan paginación.

### Pagos y Garantías
- Creación de `Payment` asocia a usuario/propiedad/metodo y retorna estado `success=true`.
- `POST /api/guarantees/{id}/release/` cambia estado de la garantía y genera registro/auditoría.

### Reseñas
- CRUD de `Review` permite valorar propiedades/usuarios según diseño; respuestas usan el envoltorio estándar.

### Zonas
- `GET /api/zones/stats/` y `GET /api/zones/zone_stats/` reflejan métricas actualizadas por señales.
- `GET /api/zones/nearby_zones/` calcula proximidad por geodistancia.

---

## Contratos de API (Lo que se espera)

### Éxito
```
{
  "success": true,
  "message": "Operación realizada",
  "data": { /* payload específico */ }
}
```

### Error de validación
```
{
  "success": false,
  "message": "Validation error",
  "data": {
    "field_name": ["mensaje de error"]
  }
}
```

### Listados con paginación
```
{
  "success": true,
  "message": null,
  "data": {
    "count": 123,
    "next": "https://.../endpoint/?page=3",
    "previous": null,
    "results": [ /* items */ ]
  }
}
```

---

## Requisitos No Funcionales
- Rendimiento: 
  - Endpoints simples (CRUD): mediana < 300ms bajo carga moderada.
  - Búsqueda/mapa: mediana < 800ms con filtros geoespaciales.
- Escalabilidad: matching intensivo se delega a tareas Celery; operaciones síncronas deben ser rápidas.
- Observabilidad: log de eventos clave (creación de propiedad, aceptación de match, release de garantía) con contexto de usuario y recurso.
- Seguridad: 
  - Autenticación por JWT; endpoints críticos requieren `IsAuthenticated`.
  - Datos sensibles (PII) protegidos; sanitización de entradas.
- Subidas: limitar tamaño de imágenes y validar formato; política configurable.
- Paginación obligatoria en listados para evitar respuestas muy grandes.

---

## Historias de Usuario (resumen)
- Como inquilino, quiero crear un perfil de búsqueda con ubicación y presupuesto para recibir recomendaciones relevantes.
- Como propietario, quiero publicar propiedades y ver interés (matches/ mensajes) para alquilar rápido.
- Como inquilino, quiero aceptar un match y contactar al propietario sin salir de la app.
- Como usuario, quiero subir y actualizar mi foto de perfil y ver su historial.
- Como administrador, quiero consultar estadísticas por zona para entender la demanda.

---

## Definición de Hecho (DoD)
- Endpoints implementados con respuestas `{ success, message, data }` y errores consistentes.
- Tests actualizados/pasando para cada flujo clave (registro, perfil, propiedades, matching, mensajes, pagos, garantías).
- Documentación de endpoints y parámetros en este PRD y/o `API_DOCUMENTATION.md`.
- Paginación y filtros verificados en listados principales.
- Métricas clave medibles y eventos logueados.

---

## Supuestos
- Paginación DRF habilitada; `page` como parámetro estándar.
- Coordenadas en WGS84 y radios en kilómetros.
- Precios como `Decimal` y monedas locales sin conversión automática.
- Autenticación por JWT con `/api/login/` y `/api/refresh/` operativos.

---

## Fuera de Alcance (fase actual)
- Pasarela de pagos externa y conciliación automática (ver Roadmap).
- Tiempo real (WebSockets) para notificaciones y chat (ver Roadmap).
- Moderación avanzada y verificación documental de agentes.