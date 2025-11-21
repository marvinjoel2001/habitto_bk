# 🧑‍🤝‍🧑 Sistema de Match de Roommates — Documentación Técnica

## Visión General
- Objetivo: conectar usuarios compatibles para compartir vivienda en base a zonas, presupuesto y preferencias personales.
- Entidades clave: `SearchProfile` del usuario y `Match` de tipo `roommate`.
- Persistencia: los matches se almacenan con `score` (0–100), `metadata.details` y `status` (`pending|accepted|rejected`).

## Modelos Relacionados
- `SearchProfile` incluye campos específicos para roomie:
  - `roommate_preference` (`no|looking|open`) — matching/models.py:18
  - `roommate_preferences` (JSON: `gender`, `smoker_ok`, etc.) — matching/models.py:19
  - `preferred_zones`, `budget_min`, `budget_max`, `vibes` — matching/models.py:8–21
- `Property` incluye campos para roomie listings:
  - `is_roomie_listing` — property/models.py:53
  - `roomie_profile` — property/models.py:54
- `Match`:
  - `match_type='roommate'`, `subject_id=<id del otro SearchProfile>`, `target_user=<User>` — matching/models.py:60–70

## Generación de Matches de Roomie
- Cálculo de compatibilidad: `calculate_roommate_match_score(profile1, profile2)` — utils/matching.py:150–173
  - Pesos: `zone 40%`, `budget 30%`, `prefs/vibes 30%` — utils/matching.py:173
- Creación on-demand: `create_roommate_matches_for_profile(profile)` — utils/matching.py:236–242
  - Usa `subject_id` como el `id` del otro `SearchProfile` — utils/matching.py:240–241
  - Persistencia condicionada por `MATCH_MIN_SCORE` (umbral global) — utils/matching.py:12, 205

## Algoritmo de Compatibilidad
- Zonas (`40%`):
  - Solapamiento entre `preferred_zones` de ambos perfiles; si faltan zonas, se usa 50 por defecto — utils/matching.py:152–156
- Presupuesto (`30%`):
  - `budget_overlap > 0` → `100`; si no, penalización proporcional — utils/matching.py:158–162
- Preferencias/Vibes (`30%`):
  - Preferencias de roommate (género, fumador) con deducciones acumulativas — utils/matching.py:164–169
  - Compatibilidad de `vibes` por intersección — utils/matching.py:170–171
- Score final: suma ponderada y detalles en `metadata.details` — utils/matching.py:173, 147

## Endpoints y Flujos

### 1. Modificación del endpoint de propiedades para incluir roomie seekers
- `GET /api/properties/?include_roomies=true`
  - Incluye tanto propiedades regulares como usuarios buscando roomie
  - Los roomie seekers aparecen con estructura especial (type='roomie_seeker')
  - Cada roomie incluye información completa del perfil en `roomie_seeker_info`
  - Implementado en property/views.py:83–110

### 2. Flujo para inquilinos que aceptan roomies
- `POST /api/matches/{id}/owner_accept/`
  - Si el inquilino tiene `roommate_preference` en ['looking', 'open'] y la propiedad permite roomies (`allows_roommates=True`)
  - Automáticamente convierte la propiedad en roomie listing
  - Crea la relación `prop.roomie_profile = tenant_profile`
  - Notifica al inquilino que su búsqueda ha sido publicada
  - Implementado en matching/views.py:378–390

### 3. Conversión manual de propiedad a roomie listing
- `POST /api/properties/{id}/convert-to-roomie/`
  - Convierte una propiedad específica en publicación de roomie
  - Requiere `tenant_profile_id` en el body
  - Solo disponible para propietarios de la propiedad
  - Valida que la propiedad permita roomies
  - Implementado en property/views.py:187–234

### 4. Búsqueda independiente de roomies
- `GET /api/roomie_search/available/`
  - Lista usuarios que buscan roomie y NO tienen propiedad asignada
  - Devuelve resultados en formato de propiedades (compatible con frontend)
  - Incluye información completa del perfil en `roomie_seeker_info`
  - Implementado en matching/views.py:119–139

- `GET /api/roomie_search/all-seekers/`
  - Lista TODOS los usuarios que buscan roomie (con o sin propiedad)
  - Útil para estadísticas o búsquedas generales
  - Implementado en matching/views.py:141–155

### 5. Endpoints existentes de roomie
- Listado de matches de roomie del perfil:
  - `GET /api/search_profiles/{id}/matches/?type=roommate&status=pending|accepted|rejected`
  - Genera/actualiza antes de listar y ordena por score — matching/views.py:52–63
- Recomendaciones de roomie:
  - `GET /api/recommendations/?type=roommate` o `type=mixed`
  - Devuelve hasta 20 con `match` serializado y `metadata.details` — matching/views.py:399–403
- Interacciones con match:
  - `POST /api/matches/{id}/like/` — like y posible auto-aceptación según reglas generales
  - `POST /api/matches/{id}/accept/` — cambia a `accepted` y abre conversación
  - `POST /api/matches/{id}/reject/` — marca `rejected` y registra `MatchFeedback`
  - Implementadas de forma genérica para cualquier `match_type` — matching/views.py:118–227

## Estructura de Datos

### RoomieSeekerPropertySerializer
```json
{
  "id": 123,
  "type": "roomie_seeker",
  "address": "Buscando en: Zona Norte, Zona Sur",
  "description": "Buscando roomie - Presupuesto: $500 - $800 | Intereses: deportista, estudiante | Prefiere: any",
  "price": 800,
  "bedrooms": 1,
  "bathrooms": 1,
  "size": 0,
  "zone_id": 1,
  "zone_name": "Zona Norte",
  "latitude": -16.5,
  "longitude": -68.1,
  "is_active": true,
  "is_roomie_listing": true,
  "roomie_seeker_info": {
    "user_id": 45,
    "roommate_preference": "looking",
    "roommate_preferences": {"gender": "any", "smoker_ok": false},
    "budget_min": "500.00",
    "budget_max": "800.00",
    "vibes": ["deportista", "estudiante"],
    "preferred_zones": [1, 2],
    // ... más campos del SearchProfile
  },
  "main_photo": null,
  "nearby_properties_count": 0,
  "amenities": [],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

## Campos Clave en SearchProfile (Roomie)
- `roommate_preference`: define intención (no busca, buscando, abierto) — matching/models.py:18
- `roommate_preferences` JSON: ejemplo
  ```json
  {
    "gender": "any",
    "smoker_ok": false,
    "quiet_hours": [22, 7]
  }
  ```
- `vibes`: lista de etiquetas personales (p.ej., "ordenado", "extrovertido") — matching/models.py:20

## Ejemplos de Uso

### 1. Obtener propiedades incluyendo roomie seekers
```http
GET /api/properties/?include_roomies=true
```

### 2. Crear/actualizar SearchProfile con preferencias de roomie
```http
POST /api/search_profiles/
{
  "budget_min": "800.00",
  "budget_max": "1200.00",
  "preferred_zones": [1, 2],
  "roommate_preference": "looking",
  "roommate_preferences": { "gender": "any", "smoker_ok": false },
  "vibes": ["ordenado", "deportista"]
}
```

### 3. Convertir propiedad a roomie listing (manual)
```http
POST /api/properties/123/convert-to-roomie/
{
  "tenant_profile_id": 45
}
```

### 4. Obtener roomies disponibles (sin propiedad asignada)
```http
GET /api/roomie_search/available/
```

### 5. Obtener todos los roomie seekers
```http
GET /api/roomie_search/all-seekers/
```

### 6. Obtener recomendaciones de roomie
```http
GET /api/recommendations/?type=roommate
```

### 7. Listar matches de roomie del perfil
```http
GET /api/search_profiles/1/matches/?type=roommate&status=pending
```

### 8. Interacciones con matches
```http
POST /api/matches/123/like/
POST /api/matches/123/accept/
POST /api/matches/123/reject/
```

## Flujo Completo de Roomie Automático

1. **Inquilino con roomie preference** da like a propiedad que permite roomies
2. **Propietario acepta el match** vía `POST /api/matches/{id}/owner_accept/`
3. **Sistema detecta** que inquilino busca roomie y propiedad permite roomies
4. **Propiedad se convierte automáticamente** en roomie listing
5. **Inquilino recibe notificación** de que su búsqueda fue publicada
6. **Propiedad aparece** en búsquedas de otros roomie seekers

## Umbral y Testing
- `MATCH_MIN_SCORE` configurable en `settings` o variable de entorno — bk_habitto/settings.py:330
- Para pruebas amplias: setear `MATCH_MIN_SCORE=0` permite almacenar todos los matches y obtener recomendaciones sin filtrar.

## Chats y Notificaciones
- Al `accept` en cualquier match se crea conversación y notificación — matching/views.py:172–207
- WebSockets: notificaciones en tiempo real ya integradas para eventos de match y likes.
- Notificaciones específicas para roomie listings cuando se crean automáticamente.

## Seguridad y Autenticación
- JWT requerido para endpoints protegidos.
- Autorización por propietario del perfil en consultas/modificaciones.
- Solo propietarios pueden convertir sus propiedades a roomie listings.

## Errores Comunes
- `401 Unauthorized`: sin token o sesión.
- `403 Forbidden`: usuario no autorizado para el recurso.
- `404 Not Found`: perfil o match inexistente.
- `400 Bad Request`: parámetros inválidos (p.ej., `type` fuera de rango).
- `400 Bad Request`: propiedad no permite roomies al intentar convertir.

## Rendimiento
- Límite de candidatos: hasta 500 perfiles evaluados por generación — utils/matching.py:236–239.
- Regeneración on-demand en listados y recomendaciones — matching/views.py:52–61, 399–407.
- Considerar caching si el tráfico crece.

## Referencias de Código
- `utils/matching.py`: cálculo y generación de roomie — utils/matching.py:150–173, 236–242.
- `matching/models.py`: `SearchProfile` y `Match` — matching/models.py:6–21, 60–70.
- `matching/views.py`: endpoints de matches y recomendaciones — matching/views.py:52–63, 399–407.
- `property/views.py`: listado con roomie seekers y conversión de propiedades — property/views.py:83–110, 187–234.
- `property/serializers.py`: serializadores para roomie seekers — property/serializers.py:98–195.
- `property/models.py`: campos de roomie listing — property/models.py:53–54.