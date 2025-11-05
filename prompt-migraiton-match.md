Quiero que actualices mi backend existente basado en la documentación API proporcionada (que incluye endpoints para usuarios, perfiles, propiedades, fotos, amenidades, garantías, incentivos, reglas de incentivos, zonas con GIS, pagos, métodos de pago, reseñas, notificaciones y mensajería). El backend actual ya maneja autenticación JWT, coordenadas geográficas con PointField, polígonos en zonas, filtrados avanzados, paginación, y respuestas estandarizadas en formato JSON con "success", "message" y "data".
Necesito que realices las siguientes modificaciones y agregues nuevas estructuras, modelos, endpoints y lógica para implementar un sistema de match inteligente inspirado en Tinder, que conecte inquilinos con propiedades, roomies (compañeros de alquiler) y agentes. El sistema debe ser gamificado con swiping, scores de compatibilidad, feedback para mejorar recomendaciones, y integración con los módulos existentes como zonas GIS para matches basados en ubicación, incentivos para motivar matches en zonas de alta demanda, y notificaciones para alertas en tiempo real.
🎯 OBJETIVO PRINCIPAL
Transformar la plataforma actual de alquileres en un sistema inteligente de matching que:

Facilite "encontrar el lugar ideal" de forma adictiva y sencilla (swiping como Tinder).
Soporte tres tipos de usuarios: inquilinos (buscadores), propietarios (listadores), y agentes (facilitadores con comisiones reducidas).
Integre roomie matching para compartir alquileres, reduciendo costos en Santa Cruz (donde el alquiler promedio es ~3,358 BOB).
Use IA rule-based para scores, con opción a embeddings semánticos para descripciones.
Mejore el engagement (basado en estudios: gamificación aumenta retención 48%, matching mutuo reduce ansiedad en mudanzas 30-50%).
Genere ingresos vía comisiones (5% app, 2-3% agentes) y premium features (e.g., super likes).

El resultado debe ser un backend escalable, seguro, con migraciones, y listo para frontend móvil/web (e.g., Flutter/React).
🧩 1. NUEVOS MODELOS Y MODIFICACIONES A EXISTENTES
Usa Django models con las convenciones actuales (e.g., PointField para locations, JSONFields para metadata flexible). Asegura compatibilidad con PostGIS para GIS queries.
A) Nuevo Modelo: SearchProfile (perfil de búsqueda para inquilinos/roomies)
pythonclass SearchProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # FK a User existente
    preferred_zones = models.ManyToManyField(Zone)  # Relación con Zone existente
    location = gis_models.PointField(null=True, blank=True)  # PointField como en Property
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    desired_types = models.JSONField(default=list)  # e.g., ['casa', 'departamento']
    bedrooms_min = models.IntegerField(null=True)
    bedrooms_max = models.IntegerField(null=True)
    amenities = models.ManyToManyField(Amenity)  # Relación con Amenity existente
    pet_allowed = models.BooleanField(default=False)
    wfh_preference = models.BooleanField(default=False)  # Work-from-home friendly
    roommate_preference = models.CharField(max_length=20, choices=[('no', 'No'), ('looking', 'Buscando'), ('open', 'Abierto')])
    roommate_preferences = models.JSONField(default=dict)  # e.g., {'gender': 'any', 'smoker_ok': True, 'max_roommates': 3}
    vibes = models.JSONField(default=list)  # e.g., ['tranquilo', 'cerca_trabajo'] para matching semántico
    semantic_embedding = models.TextField(null=True)  # Para embeddings IA opcionales
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
B) Nuevo Modelo: RoommateRequest (solicitudes para roomies)
pythonclass RoommateRequest(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(SearchProfile, on_delete=models.CASCADE, related_name='roommate_requests')
    desired_move_in_date = models.DateField(null=True)
    max_roommates = models.IntegerField(default=2)
    gender_preference = models.CharField(max_length=20, choices=[('male', 'Hombres'), ('female', 'Mujeres'), ('any', 'Cualquiera')], default='any')
    smoker_ok = models.BooleanField(default=False)
    budget_per_person = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
C) Nuevo Modelo: Match (almacena matches calculados)
pythonclass Match(models.Model):
    id = models.AutoField(primary_key=True)
    match_type = models.CharField(max_length=20, choices=[('property', 'Property'), ('roommate', 'Roommate'), ('agent', 'Agent')])
    subject_id = models.IntegerField()  # ID de Property, RoommateRequest o Agent (User)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.FloatField()  # 0-100
    metadata = models.JSONField(default=dict)  # Explicación del score, e.g., {'location_score': 90, 'reason': 'Cerca de tu zona preferida'}
    status = models.CharField(max_length=20, choices=[('pending', 'Pendiente'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
D) Nuevo Modelo: MatchFeedback (feedback para refinar IA)
pythonclass MatchFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=20, choices=[('like', 'Like'), ('dislike', 'Dislike'), ('neutral', 'Neutral')])
    reason = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
E) Modificaciones a Modelos Existentes:

Property: Agrega campos para matching:
pythonallows_roommates = models.BooleanField(default=False)
max_occupancy = models.IntegerField(null=True)
min_price_per_person = models.DecimalField(max_digits=12, decimal_places=2, null=True)
is_furnished = models.BooleanField(default=False)
tenant_requirements = models.JSONField(default=dict)  # e.g., {'pet_allowed': True, 'smoker_ok': False}
tags = models.JSONField(default=list)  # e.g., ['tranquilo', 'cerca_centro']
semantic_embedding = models.TextField(null=True)  # Para matching avanzado

User/Profile: Agrega campos para agentes/roomies:
pythonis_agent = models.BooleanField(default=False)  # Para identificar agentes
agent_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)  # e.g., 2%
roommate_vibes = models.JSONField(default=dict)  # Para matching personal

Zone: Agrega stats para matching (integra con existentes):
pythonmatch_activity_score = models.FloatField(default=0.0)  # Calculado de matches en la zona


⚙️ 2. NUEVOS ENDPOINTS
Mantén el formato de respuestas JSON estándar ("success", "message", "data"). Usa JWT auth en todos. Integra con GIS para location-based matches.

POST /api/search_profiles/: Crea/actualiza SearchProfile (one-to-one con User). Valida campos GIS como latitude/longitude.
GET /api/search_profiles/my/: Obtiene el SearchProfile del usuario autenticado.
GET /api/search_profiles/{id}/matches/?type=property|roommate|agent&page=1&page_size=20: Lista matches paginados, ordenados por score descendente. Incluye metadata con explicación.
POST /api/roommate_requests/: Crea solicitud basada en SearchProfile.
GET /api/roommate_requests/my/: Lista solicitudes del usuario.
POST /api/matches/{match_id}/accept/: Actualiza status a 'accepted', envía notificación/mensaje, y si es property, inicia garantía/pago.
POST /api/matches/{match_id}/reject/: Actualiza status, guarda reason para feedback.
POST /api/match_feedback/: Guarda feedback para refinar algoritmos futuros.
GET /api/recommendations/?type=mixed&page=1: Recomendaciones híbridas (propiedades + roomies + agentes), usando IA para personalizar.

🔁 3. MODIFICACIONES A ENDPOINTS EXISTENTES

POST /api/properties/: Valida nuevos campos (allows_roommates, etc.). Tras creación, triggera matches automáticos con SearchProfiles cercanos (usando GIS query para zonas próximas).
GET /api/properties/: Agrega filtro 'match_score' (calculado on-the-fly para usuario autenticado).
GET /api/zones/{id}/stats/: Agrega 'match_ratio' (matches aceptados/vistos) y 'roomie_demand' (basado en RoommateRequests).
POST /api/incentives/generate/: Integra con matches – e.g., incentivos para zonas con bajo match_ratio o alta demanda de roomies.
POST /api/notifications/: Auto-genera para matches (e.g., "¡Nuevo match con propiedad en tu zona!").
POST /api/messages/: Auto-crea conversaciones post-match (e.g., tripartito con agente si aplica).

🧠 4. ALGORITMO DE MATCHING (Rule-Based con Opcional IA)
Implementa funciones reutilizables en utils/matching.py. Usa PostGIS para distancias (e.g., ST_Distance).
A) Para Propiedades:
pythondef calculate_property_match_score(search_profile, property):
    # 1. Location Score: Distancia GIS
    if search_profile.location and property.location:
        distance_km = search_profile.location.distance(property.location) * 100  # Aproximado km
        location_score = max(0, 100 - (distance_km * 10))  # Penaliza >10km
    else:
        location_score = 50  # Neutral si no hay coords

    # 2. Price Score: Rango + roomie option
    price_score = 100 if search_profile.budget_min <= property.price <= search_profile.budget_max else max(0, 100 - abs(property.price - search_profile.budget_max) / search_profile.budget_max * 100)
    if property.allows_roommates and search_profile.roommate_preference != 'no':
        per_person = property.price / property.max_occupancy
        price_score = max(price_score, 100 if per_person <= search_profile.budget_max else 80)

    # 3. Amenities Score: Coincidencias
    matching_amenities = set(search_profile.amenities.all()) & set(property.amenities.all())
    amenities_score = len(matching_amenities) / len(search_profile.amenities.all()) * 100 if search_profile.amenities.exists() else 100

    # 4. Roommate/Vibes Score: Compatibilidad
    roommate_score = 100 if (property.allows_roommates == (search_profile.roommate_preference != 'no')) else 50
    vibes_score = len(set(search_profile.vibes) & set(property.tags)) / len(search_profile.vibes) * 100 if search_profile.vibes else 100

    # 5. Reputation/Freshness: Reviews y fecha
    reputation_score = property.reviews.aggregate(avg=Avg('rating'))['avg'] * 20 if property.reviews.exists() else 80
    freshness_score = max(0, 100 - (now() - property.created_at).days * 2)  # Penaliza propiedades antiguas

    # Pesos (ajustables vía admin)
    weights = {'location': 0.3, 'price': 0.25, 'amenities': 0.15, 'roommate': 0.15, 'reputation': 0.1, 'freshness': 0.05}
    total_score = sum(locals()[f"{key}_score"] * weights[key] for key in weights)

    return round(total_score, 2), {'details': {f"{key}_score": locals()[f"{key}_score"] for key in weights}}
B) Para Roomies:
pythondef calculate_roommate_match_score(profile1, profile2):
    # 1. Location/Zones: Coincidencia en zonas preferidas
    zone_match = len(set(profile1.preferred_zones.all()) & set(profile2.preferred_zones.all())) / max(len(profile1.preferred_zones.all()), 1) * 100

    # 2. Budget: Compatibilidad per-person
    budget_overlap = min(profile1.budget_max, profile2.budget_max) - max(profile1.budget_min, profile2.budget_min)
    budget_score = 100 if budget_overlap > 0 else max(0, 100 - abs(profile1.budget_max - profile2.budget_min) / profile1.budget_max * 100)

    # 3. Preferences: Gender, smoker, vibes
    prefs_score = 100
    if profile1.roommate_preferences['gender'] != 'any' and profile1.roommate_preferences['gender'] != profile2.gender:
        prefs_score -= 50
    if not profile1.roommate_preferences['smoker_ok'] and profile2.smoker:
        prefs_score -= 30
    vibes_match = len(set(profile1.vibes) & set(profile2.vibes)) / len(profile1.vibes) * 100 if profile1.vibes else 100
    prefs_score = (prefs_score + vibes_match) / 2

    # Pesos
    weights = {'zone': 0.4, 'budget': 0.3, 'prefs': 0.3}
    total_score = sum(locals()[f"{key}_score"] * weights[key] for key in weights)

    return round(total_score, 2), {'details': {f"{key}_score": locals()[f"{key}_score"] for key in weights}}
C) Para Agentes: Similar a propiedades, pero basado en expertise (e.g., zonas manejadas, commission_rate baja).

Trigger: Calcula matches on-demand o batch (cron diario).
Almacena en Match si score > 70, con metadata para explicación.

🧮 5. ARQUITECTURA Y OPTIMIZACIONES

Realtime Matching: Usa Celery tasks para calcular scores async al crear/update SearchProfile o Property.
Batch Processing: Cron job nightly para recalcular matches masivos, usando feedback para ajustar pesos (e.g., si muchos dislikes en location, baja peso).
Cache: Redis para scores frecuentes (e.g., cache_key = f"match_{user_id}_{property_id}").
GIS Integración: Usa ST_Within/ST_Distance para matches cerca (integra con /api/zones/find_by_location/).
Escalabilidad: Paginate results, limit swipes diarios para evitar abuso (comportamiento: previene burnout).
Background Jobs: Celery para notificaciones, incentivos post-match (e.g., bono por match aceptado).

💬 6. NOTIFICACIONES, MENSAJERÍA E INCENTIVOS

Post-match: Envía notificación ("¡Match con depa ideal! Score 85%") y crea mensaje automático.
Feedback: Usa para refinar (e.g., si dislike por price, ajusta filtros futuros).
Incentivos: Triggera en matches bajos en zonas (integra con /api/incentive-rules/generate/, e.g., "Bono 5% por match en zona baja demanda").

🤖 7. USO DE IA EXTERNA (OPCIONAL, NO DEPENDIENTE)

Solo para semántica: Usa OpenAI/Gemini para generar embeddings de descripciones/vibes (almacena en semantic_embedding).
Prompt ejemplo: "Extrae keywords de esta descripción: [text]" para tags.
No uses IA para core matching – mantén rule-based para control y costos.

🧱 8. SEGURIDAD Y PERMISOS

JWT obligatorio; verifica ownership (e.g., solo user ve sus matches).
Rate limiting en swiping (e.g., 100/día).
Privacidad: Anonimiza likes hasta match mutuo.
Validaciones: Asegura property existe, user verificado, no self-match.

🚀 9. MIGRACIÓN, TESTING Y DEPLOY

Genera migraciones para nuevos modelos y alteraciones (e.g., add_field a Property).
Tests: Unitarios para calculate_match_score, integrales para endpoints (e.g., crea profile → get matches → assert score).
MVP Flow: Registro → Perfil → Swiping → Match → Feedback.
Deploy: Actualiza requirements (si necesitas pgvector/Celery), prepara rollback.

👉 INSTRUCCIONES FINALES PARA EL IDE/ASISTENTE IA:

Analiza la documentación API actual (endpoints como /api/properties/, /api/zones/, etc.) para integrar sin romper.
Genera código Django completo: models, serializers, views, urls, utils (matching.py).
Actualiza OpenAPI docs con nuevos endpoints.
Implementa el algoritmo con ejemplos de tests.
Asegura compatibilidad con GIS (PointField, polygons).
Output: Código estructurado por archivos (models.py, views.py, etc.), más migraciones SQL.
