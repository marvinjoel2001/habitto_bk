from typing import Tuple, Dict
from django.utils.timezone import now
from django.db.models import Avg
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from matching.models import Match, SearchProfile, RoommateRequest
from property.models import Property
from zone.models import Zone
from django.contrib.auth.models import User


def calculate_property_match_score(search_profile: SearchProfile, property_obj: Property) -> Tuple[float, Dict]:
    # 1. Location Score: Distancia GIS
    if search_profile.location and property_obj.location:
        try:
            # Aproximado en kilómetros usando distancia geodésica simple
            distance_km = search_profile.location.distance(property_obj.location) * 100
        except Exception:
            distance_km = 0
        location_score = max(0, 100 - (distance_km * 10))
    else:
        location_score = 50

    # 2. Price Score
    price_score = 80
    if search_profile.budget_min is not None and search_profile.budget_max is not None:
        price = float(property_obj.price)
        min_b = float(search_profile.budget_min)
        max_b = float(search_profile.budget_max)
        if min_b <= price <= max_b:
            price_score = 100
        else:
            diff = abs(price - max_b) / max(max_b, 1)
            price_score = max(0, 100 - diff * 100)
    if getattr(property_obj, 'allows_roommates', False) and search_profile.roommate_preference != 'no':
        if getattr(property_obj, 'max_occupancy', None):
            per_person = float(property_obj.price) / max(property_obj.max_occupancy, 1)
            if search_profile.budget_max is not None:
                price_score = max(price_score, 100 if per_person <= float(search_profile.budget_max) else 80)

    # 3. Amenities Score
    try:
        s_amenities = set(search_profile.amenities.all())
        p_amenities = set(property_obj.amenities.all())
        matching_amenities = s_amenities & p_amenities
        amenities_score = (len(matching_amenities) / max(len(s_amenities), 1)) * 100 if s_amenities else 100
    except Exception:
        amenities_score = 100

    # 4. Roommate/Vibes Score
    roommate_score = 100 if (getattr(property_obj, 'allows_roommates', False) == (search_profile.roommate_preference != 'no')) else 50
    try:
        vibes_score = (len(set(search_profile.vibes) & set(getattr(property_obj, 'tags', []))) / max(len(search_profile.vibes), 1)) * 100 if search_profile.vibes else 100
    except Exception:
        vibes_score = 100

    # 5. Reputation/Freshness
    try:
        avg_rating = property_obj.reviews.aggregate(avg=Avg('rating'))['avg']
        reputation_score = float(avg_rating) * 20 if avg_rating else 80
    except Exception:
        reputation_score = 80
    freshness_days = (now() - property_obj.created_at).days if property_obj.created_at else 0
    freshness_score = max(0, 100 - (freshness_days * 2))

    # 6. Factor familiar: si tiene hijos y la propiedad tiene suficientes dormitorios
    try:
        children = int(getattr(search_profile, 'children_count', 0) or 0)
        fam_need_bedrooms = children >= 1
        bedrooms_ok = bool(getattr(property_obj, 'bedrooms', 0) >= (2 if fam_need_bedrooms else 1))
        family_score = 100 if bedrooms_ok else 60
    except Exception:
        family_score = 80

    weights = {'location': 0.28, 'price': 0.24, 'amenities': 0.15, 'roommate': 0.14, 'reputation': 0.09, 'freshness': 0.05, 'family': 0.05}
    total_score = sum([
        location_score * weights['location'],
        price_score * weights['price'],
        amenities_score * weights['amenities'],
        roommate_score * weights['roommate'],
        reputation_score * weights['reputation'],
        freshness_score * weights['freshness'],
        family_score * weights['family'],
    ])
    details = {
        'location_score': round(location_score, 2),
        'price_score': round(price_score, 2),
        'amenities_score': round(amenities_score, 2),
        'roommate_score': round(roommate_score, 2),
        'reputation_score': round(reputation_score, 2),
        'freshness_score': round(freshness_score, 2),
        'family_score': round(family_score, 2),
    }
    return round(total_score, 2), {'details': details}


def calculate_roommate_match_score(profile1: SearchProfile, profile2: SearchProfile) -> Tuple[float, Dict]:
    try:
        zones1 = set(profile1.preferred_zones.all())
        zones2 = set(profile2.preferred_zones.all())
        zone_match = (len(zones1 & zones2) / max(len(zones1), 1)) * 100 if zones1 else 50
    except Exception:
        zone_match = 50

    budget_score = 80
    if profile1.budget_max and profile2.budget_max and profile1.budget_min and profile2.budget_min:
        budget_overlap = float(min(profile1.budget_max, profile2.budget_max)) - float(max(profile1.budget_min, profile2.budget_min))
        budget_score = 100 if budget_overlap > 0 else max(0, 80 - abs(float(profile1.budget_max) - float(profile2.budget_min)) / max(float(profile1.budget_max), 1) * 100)

    prefs_score = 100
    p1 = profile1.roommate_preferences or {}
    p2 = profile2.roommate_preferences or {}
    if p1.get('gender') not in [None, 'any'] and p1.get('gender') != p2.get('gender'):
        prefs_score -= 50
    if not p1.get('smoker_ok', True) and p2.get('smoker', False):
        prefs_score -= 30
    vibes_match = (len(set(profile1.vibes) & set(profile2.vibes)) / max(len(profile1.vibes), 1)) * 100 if profile1.vibes else 100
    prefs_score = (prefs_score + vibes_match) / 2

    weights = {'zone': 0.4, 'budget': 0.3, 'prefs': 0.3}
    total_score = sum([
        zone_match * weights['zone'],
        budget_score * weights['budget'],
        prefs_score * weights['prefs'],
    ])
    details = {
        'zone_score': round(zone_match, 2),
        'budget_score': round(budget_score, 2),
        'prefs_score': round(prefs_score, 2),
    }
    return round(total_score, 2), {'details': details}


def calculate_agent_match_score(profile: SearchProfile, agent: User) -> Tuple[float, Dict]:
    # Simple heurística basada en comisión y zonas preferidas
    up = getattr(agent, 'profile', None)
    commission = float(getattr(up, 'agent_commission_rate', 2.0) or 2.0)
    is_agent = bool(getattr(up, 'user_type', '') == 'agente' or getattr(up, 'is_agent', False))
    base = 50 if is_agent else 0
    commission_score = max(0, 100 - commission * 10)  # Menor comisión => mayor score
    zones_overlap = 0
    try:
        agent_zones = set(getattr(up, 'managed_zones', []))  # Placeholder; si existe relación futura
        zones_overlap = (len(agent_zones & set(profile.preferred_zones.all())) / max(len(profile.preferred_zones.all()), 1)) * 100 if profile.preferred_zones.exists() else 50
    except Exception:
        zones_overlap = 50
    total_score = base * 0.4 + commission_score * 0.4 + zones_overlap * 0.2
    return round(total_score, 2), {'details': {'commission_score': commission_score, 'zones_overlap': zones_overlap}}


def _store_match(match_type: str, subject_id: int, target_user: User, score: float, metadata: Dict):
    if score >= 70:
        Match.objects.update_or_create(
            match_type=match_type,
            subject_id=subject_id,
            target_user=target_user,
            defaults={'score': score, 'metadata': metadata}
        )
        # Actualizar actividad de zona si corresponde
        if match_type == 'property':
            try:
                prop = Property.objects.get(id=subject_id)
                if prop.zone:
                    z = prop.zone
                    z.match_activity_score = float(getattr(z, 'match_activity_score', 0.0) or 0.0) + (score / 100.0)
                    z.save(update_fields=['match_activity_score'])
            except Property.DoesNotExist:
                pass


def create_property_matches_for_profile(profile: SearchProfile):
    qs = Property.objects.filter(is_active=True)
    if profile.location:
        try:
            qs = qs.filter(location__distance_lte=(profile.location, Distance(km=10)))
        except Exception:
            pass
    for prop in qs[:500]:  # limitar por rendimiento
        score, meta = calculate_property_match_score(profile, prop)
        _store_match('property', prop.id, profile.user, score, meta)


def create_roommate_matches_for_profile(profile: SearchProfile):
    others = SearchProfile.objects.exclude(user=profile.user)
    for other in others[:500]:
        score, meta = calculate_roommate_match_score(profile, other)
        # Usamos subject_id como el id del otro perfil para roomie
        _store_match('roommate', other.id, profile.user, score, meta)


def create_agent_matches_for_profile(profile: SearchProfile):
    agents = User.objects.filter(profile__user_type='agente')
    for agent in agents[:200]:
        score, meta = calculate_agent_match_score(profile, agent)
        _store_match('agent', agent.id, profile.user, score, meta)