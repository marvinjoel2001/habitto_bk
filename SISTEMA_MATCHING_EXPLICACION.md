# 🎯 Sistema de Matching de Habitto - Explicación Completa

## ¿Qué es el Sistema de Matching?

El sistema de matching es como un **"Tinder para propiedades y roommates"**. Conecta automáticamente a usuarios con propiedades, compañeros de cuarto (roommates) y agentes inmobiliarios basándose en sus preferencias y compatibilidad.

---

## 📋 Componentes Principales

### 1. **SearchProfile** (Perfil de Búsqueda)
Es el "perfil de preferencias" de cada usuario. Contiene toda la información sobre lo que busca:

**Información Básica:**
- 📍 **Ubicación**: Dónde quiere vivir (coordenadas GPS)
- 💰 **Presupuesto**: Rango de precio (mínimo y máximo)
- 🏠 **Tipo de propiedad**: Casa, departamento, habitación, anticrético
- 🛏️ **Dormitorios**: Cantidad mínima y máxima

**Preferencias Adicionales:**
- 🎯 **Amenidades**: Piscina, gimnasio, garaje, etc.
- 🐕 **Mascotas**: Si permite mascotas
- 💼 **Trabajo remoto**: Si necesita espacio para home office
- 👥 **Roommate**: Si busca compañero de cuarto, está abierto, o no quiere

**Información Personal (para mejor matching):**
- 👤 Edad, género, ocupación
- 👨‍👩‍👧‍👦 Tamaño de familia, número de hijos
- 🚗 Si tiene vehículo
- 🚭 Si fuma
- 🗣️ Idiomas que habla
- 📚 Nivel educativo
- 🎨 Estilo de vida y horarios

### 2. **Match** (Coincidencia)
Es la conexión entre un usuario y algo que le puede interesar. Tiene:

**Tipos de Match:**
- 🏠 **property**: Usuario ↔ Propiedad
- 👥 **roommate**: Usuario ↔ Otro usuario (para compartir)
- 🤝 **agent**: Usuario ↔ Agente inmobiliario

**Información del Match:**
- 📊 **Score**: Puntuación de compatibilidad (0-100)
- 📝 **Metadata**: Detalles de por qué es compatible
- ✅ **Status**: pending (pendiente), accepted (aceptado), rejected (rechazado)

### 3. **MatchFeedback** (Retroalimentación)
Guarda la opinión del usuario sobre un match:
- 👍 **like**: Le gustó
- 👎 **dislike**: No le gustó
- 😐 **neutral**: Neutral
- 💬 **reason**: Razón opcional del feedback

---

## 🔄 ¿Cómo Funciona el Matching?

### Paso 1: Usuario Crea su Perfil de Búsqueda

```http
POST /api/search_profiles/
{
  "budget_min": "800.00",
  "budget_max": "1500.00",
  "desired_types": ["casa", "departamento"],
  "bedrooms_min": 2,
  "bedrooms_max": 3,
  "latitude": "-16.500000",
  "longitude": "-68.150000",
  "amenities": [1, 2, 3],  // IDs de amenidades
  "pet_allowed": true,
  "roommate_preference": "open",
  "age": 28,
  "children_count": 0,
  "family_size": 2,
  "smoker": false
}
```

### Paso 2: Sistema Calcula Compatibilidad

Cuando el usuario pide recomendaciones o cuando se crea una nueva propiedad, el sistema calcula automáticamente el **score de compatibilidad** usando varios factores:

#### 🏠 Para Matching con Propiedades:

**1. Ubicación (28% del score)**
- Calcula distancia entre ubicación del usuario y la propiedad
- Mientras más cerca, mejor score
- Ejemplo: 2km de distancia = 80 puntos, 10km = 0 puntos

**2. Precio (24% del score)**
- Compara precio de propiedad con presupuesto del usuario
- Si está dentro del rango = 100 puntos
- Si está fuera, penaliza según qué tan lejos esté

**3. Amenidades (15% del score)**
- Cuenta cuántas amenidades deseadas tiene la propiedad
- Ejemplo: Usuario quiere 4 amenidades, propiedad tiene 3 = 75 puntos

**4. Roommate/Vibes (14% del score)**
- Si usuario busca roommate y propiedad lo permite = 100 puntos
- Compara "vibes" o etiquetas de estilo de vida

**5. Reputación (9% del score)**
- Promedio de reseñas de la propiedad
- 5 estrellas = 100 puntos, 3 estrellas = 60 puntos

**6. Frescura (5% del score)**
- Propiedades más nuevas tienen mejor score
- Recién publicada = 100 puntos, 50 días = 0 puntos

**7. Factor Familiar (5% del score)**
- Si usuario tiene hijos, verifica que haya suficientes dormitorios
- Familia con 2 hijos + propiedad de 3 dormitorios = 100 puntos

**Ejemplo de Cálculo:**
```
Usuario busca:
- Presupuesto: $800-$1500
- Ubicación: Zona Sur
- 2-3 dormitorios
- Piscina, Gimnasio

Propiedad:
- Precio: $1200 ✅
- Ubicación: 3km de distancia ✅
- 3 dormitorios ✅
- Tiene Piscina y Gimnasio ✅
- Rating: 4.5 estrellas ✅
- Publicada hace 5 días ✅

Score Final = 92/100 🎯
```

#### 👥 Para Matching con Roommates:

**1. Zonas Preferidas (40% del score)**
- Compara zonas donde ambos quieren vivir
- Más zonas en común = mejor score

**2. Presupuesto (30% del score)**
- Verifica que ambos puedan pagar un rango similar

**3. Preferencias Personales (30% del score)**
- Género preferido
- Fumador/No fumador
- Vibes o estilos de vida compatibles

#### 🤝 Para Matching con Agentes:

**1. Tipo de Usuario (40%)**
- Verifica que sea agente verificado

**2. Comisión (40%)**
- Menor comisión = mejor score

**3. Zonas que Maneja (20%)**
- Si maneja las zonas que te interesan

---

## 🎬 Flujo Completo de Uso

### Escenario: María busca departamento

**1. María crea su perfil de búsqueda**
```http
POST /api/search_profiles/
{
  "budget_min": "1000",
  "budget_max": "1800",
  "desired_types": ["departamento"],
  "bedrooms_min": 2,
  "latitude": "-16.500000",
  "longitude": "-68.150000",
  "amenities": [1, 3, 5],  // Piscina, Garaje, Internet
  "pet_allowed": true,
  "age": 32,
  "children_count": 1
}
```

**2. María pide recomendaciones**
```http
GET /api/recommendations/?type=property
```

**3. Sistema genera matches automáticamente**
- Busca todas las propiedades activas cerca de su ubicación
- Calcula score de compatibilidad con cada una
- Solo guarda matches con score >= 70
- Ordena por score (mejores primero)

**4. María recibe lista de propiedades compatibles**
```json
{
  "results": [
    {
      "type": "property",
      "match": {
        "id": 123,
        "match_type": "property",
        "subject_id": 45,  // ID de la propiedad
        "score": 92.5,
        "status": "pending",
        "metadata": {
          "details": {
            "location_score": 95,
            "price_score": 100,
            "amenities_score": 75,
            "family_score": 100
          }
        }
      }
    }
  ]
}
```

**5. María ve una propiedad que le gusta y la acepta**
```http
POST /api/matches/123/accept/
```

**6. Sistema automáticamente:**
- ✅ Cambia status del match a "accepted"
- 📧 Crea notificación para María confirmando el like
- 💬 Envía mensaje automático al propietario: "Hola, me interesa tu propiedad (match 92%)"
- 🔔 Notifica al propietario: "María está interesada en tu propiedad (match 92%)"

**7. Propietario recibe el interés y puede responder**
- Ve el mensaje de María
- Puede iniciar conversación
- Ve que es un match de 92% (alta compatibilidad)

---

## 🎯 Casos de Uso Principales

### Caso 1: Buscar Propiedades Compatibles
```http
# Opción A: Ver todas las propiedades con filtro de score
GET /api/properties/?match_score=80

# Opción B: Ver matches específicos (tipo swipe)
GET /api/search_profiles/1/matches/?type=property&status=pending
```

### Caso 2: Buscar Roommate
```http
# Crear solicitud de roommate
POST /api/roommate_requests/
{
  "desired_move_in_date": "2025-12-01",
  "max_roommates": 2,
  "gender_preference": "any",
  "smoker_ok": false,
  "budget_per_person": "600.00"
}

# Ver matches de roommates
GET /api/search_profiles/1/matches/?type=roommate
```

### Caso 3: Aceptar/Rechazar Matches
```http
# Aceptar (like)
POST /api/matches/123/accept/

# Rechazar con razón
POST /api/matches/124/reject/
{
  "reason": "Muy lejos de mi trabajo"
}
```

### Caso 4: Dar Feedback
```http
POST /api/match_feedback/
{
  "match": 123,
  "feedback_type": "like",
  "reason": "Perfecta ubicación y precio"
}
```

---

## 🔄 Generación Automática de Matches

### ¿Cuándo se generan matches?

**1. Cuando usuario pide recomendaciones:**
```http
GET /api/recommendations/?type=property
```
→ Sistema genera matches on-demand si no existen recientes

**2. Cuando se crea una nueva propiedad:**
→ Sistema busca perfiles compatibles y crea matches automáticamente

**3. Cuando usuario consulta sus matches:**
```http
GET /api/search_profiles/1/matches/?type=property
```
→ Sistema actualiza matches antes de mostrarlos

### Reglas de Almacenamiento

- ✅ Solo se guardan matches con **score >= 70**
- 🔄 Se actualizan si ya existen (no duplicados)
- 📊 Se ordenan por score (mejores primero)
- ⏱️ Se pueden regenerar on-demand

---

## 📊 Ventajas del Sistema

### Para Usuarios (Inquilinos):
- 🎯 **Recomendaciones personalizadas** basadas en sus preferencias
- ⏱️ **Ahorro de tiempo** - no buscar manualmente
- 📈 **Mejor compatibilidad** - algoritmo considera múltiples factores
- 💬 **Conexión directa** - mensaje automático al propietario

### Para Propietarios:
- 👥 **Leads calificados** - solo usuarios realmente compatibles
- 📊 **Score de compatibilidad** - saber qué tan buen match es
- 🎯 **Notificaciones automáticas** cuando alguien está interesado
- 💰 **Mayor probabilidad de alquiler** - usuarios pre-filtrados

### Para Agentes:
- 🤝 **Conexión con clientes potenciales** compatibles
- 📍 **Basado en zonas** que manejan
- 💼 **Comisión competitiva** considerada en el matching

---

## 🔧 Configuración y Personalización

### Ajustar Pesos del Algoritmo
En `utils/matching.py` puedes modificar los pesos:

```python
weights = {
    'location': 0.28,    # 28% - Ubicación
    'price': 0.24,       # 24% - Precio
    'amenities': 0.15,   # 15% - Amenidades
    'roommate': 0.14,    # 14% - Roommate
    'reputation': 0.09,  # 9% - Reputación
    'freshness': 0.05,   # 5% - Frescura
    'family': 0.05       # 5% - Factor familiar
}
```

### Cambiar Umbral Mínimo de Score
Por defecto solo se guardan matches con score >= 70:

```python
if score >= 70:  # Cambiar este valor
    _store_match(...)
```

---

## 📱 Ejemplo de Flujo en App Móvil

### Pantalla 1: Crear Perfil
```
┌─────────────────────────┐
│ 📝 Tu Perfil de Búsqueda│
├─────────────────────────┤
│ Presupuesto: $800-$1500 │
│ Ubicación: Zona Sur     │
│ Dormitorios: 2-3        │
│ Amenidades:             │
│  ☑ Piscina              │
│  ☑ Gimnasio             │
│  ☐ Garaje               │
│                         │
│ [Guardar Perfil]        │
└─────────────────────────┘
```

### Pantalla 2: Ver Matches (Swipe)
```
┌─────────────────────────┐
│ 🏠 Casa en Zona Sur     │
│ $1,200/mes              │
│                         │
│ 🎯 Match: 92%           │
│                         │
│ ✅ Piscina              │
│ ✅ Gimnasio             │
│ ✅ 3 dormitorios        │
│                         │
│ [❌ Rechazar] [💚 Like] │
└─────────────────────────┘
```

### Pantalla 3: Match Aceptado
```
┌─────────────────────────┐
│ ✅ ¡Match Aceptado!     │
│                         │
│ Hemos notificado al     │
│ propietario Juan Pérez  │
│                         │
│ Mensaje enviado:        │
│ "Hola, me interesa tu   │
│  propiedad (match 92%)" │
│                         │
│ [Ver Conversación]      │
└─────────────────────────┘
```

---

## 🎓 Resumen Ejecutivo

**El sistema de matching es un motor de recomendaciones inteligente que:**

1. 📝 **Captura** las preferencias del usuario en un SearchProfile
2. 🔍 **Analiza** propiedades, roommates y agentes disponibles
3. 🧮 **Calcula** scores de compatibilidad usando múltiples factores
4. 🎯 **Filtra** solo matches con alta compatibilidad (>= 70%)
5. 📊 **Ordena** por mejor compatibilidad primero
6. 💬 **Conecta** automáticamente usuarios con propietarios
7. 📈 **Aprende** del feedback para mejorar futuras recomendaciones

**Resultado:** Experiencia tipo Tinder para encontrar la propiedad o roommate perfecto, ahorrando tiempo y aumentando la probabilidad de éxito en el alquiler.