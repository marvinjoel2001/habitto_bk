from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from .models import Incentive, IncentiveRule, IncentiveType
from zone.models import Zone
import logging

logger = logging.getLogger(__name__)


class IncentiveService:
    """Servicio para manejar la lógica automática de incentivos"""
    
    @staticmethod
    def analyze_zone_market_conditions(zone):
        """Analiza las condiciones de mercado de una zona específica"""
        offer_count = zone.offer_count
        demand_count = zone.demand_count
        
        # Calcular métricas
        offer_demand_ratio = offer_count / max(demand_count, 1)
        activity_score = (offer_count + demand_count) / 2
        
        # Determinar condiciones del mercado
        conditions = {
            'high_demand': demand_count > 10 and offer_demand_ratio < 0.5,
            'low_supply': offer_count < 5 and demand_count > 5,
            'balanced_market': 0.5 <= offer_demand_ratio <= 2.0,
            'oversupply': offer_demand_ratio > 3.0,
            'low_activity': activity_score < 3,
            'offer_demand_ratio': offer_demand_ratio,
            'activity_score': activity_score
        }
        
        return conditions
    
    @staticmethod
    def generate_automatic_incentives():
        """Genera incentivos automáticos para todas las zonas basado en reglas"""
        generated_incentives = []
        
        # Obtener todas las reglas activas
        active_rules = IncentiveRule.objects.filter(is_active=True)
        
        # Analizar cada zona
        for zone in Zone.objects.all():
            conditions = IncentiveService.analyze_zone_market_conditions(zone)
            
            for rule in active_rules:
                if rule.check_conditions(zone):
                    # Verificar cooldown
                    if IncentiveService._is_in_cooldown(rule, zone):
                        continue
                    
                    # Generar incentivos para usuarios elegibles
                    eligible_users = IncentiveService._get_eligible_users(zone, rule.incentive_type)
                    
                    for user in eligible_users:
                        incentive = IncentiveService._create_incentive(
                            user=user,
                            zone=zone,
                            rule=rule,
                            conditions=conditions
                        )
                        if incentive:
                            generated_incentives.append(incentive)
                            logger.info(f"Incentivo automático generado: {incentive}")
        
        return generated_incentives
    
    @staticmethod
    def _is_in_cooldown(rule, zone):
        """Verifica si una regla está en período de cooldown para una zona"""
        cooldown_date = timezone.now() - timedelta(days=rule.cooldown_days)
        
        recent_incentives = Incentive.objects.filter(
            zone=zone,
            incentive_type=rule.incentive_type,
            created_at__gte=cooldown_date
        ).exists()
        
        return recent_incentives
    
    @staticmethod
    def _get_eligible_users(zone, incentive_type):
        """Obtiene usuarios elegibles para recibir incentivos en una zona"""
        # Lógica para determinar usuarios elegibles basado en el tipo de incentivo
        if incentive_type == IncentiveType.HIGH_DEMAND:
            # Propietarios con propiedades en la zona
            return User.objects.filter(
                properties__zone=zone,
                properties__is_active=True
            ).distinct()[:5]  # Limitar a 5 usuarios
            
        elif incentive_type == IncentiveType.LOW_SUPPLY:
            # Usuarios que han buscado en la zona recientemente
            return User.objects.filter(
                zonesearchlog__zone=zone,
                zonesearchlog__created_at__gte=timezone.now() - timedelta(days=30)
            ).distinct()[:10]  # Limitar a 10 usuarios
            
        elif incentive_type == IncentiveType.ZONE_PROMOTION:
            # Usuarios activos en general
            return User.objects.filter(
                is_active=True,
                last_login__gte=timezone.now() - timedelta(days=7)
            )[:3]  # Limitar a 3 usuarios
            
        return User.objects.none()
    
    @staticmethod
    def _create_incentive(user, zone, rule, conditions):
        """Crea un incentivo individual"""
        try:
            # Verificar si el usuario ya tiene un incentivo activo similar
            existing_incentive = Incentive.objects.filter(
                user=user,
                zone=zone,
                incentive_type=rule.incentive_type,
                is_active=True,
                valid_until__gt=timezone.now()
            ).exists()
            
            if existing_incentive:
                return None
            
            # Calcular monto del incentivo
            amount = rule.calculate_incentive_amount(zone)
            
            # Calcular fecha de vencimiento
            valid_until = timezone.now() + timedelta(days=rule.duration_days)
            
            # Generar descripción personalizada
            description = IncentiveService._generate_description(rule, zone, conditions)
            
            # Crear el incentivo
            incentive = Incentive.objects.create(
                user=user,
                zone=zone,
                amount=amount,
                description=description,
                incentive_type=rule.incentive_type,
                valid_until=valid_until,
                offer_demand_ratio=conditions['offer_demand_ratio'],
                zone_activity_score=conditions['activity_score']
            )
            
            return incentive
            
        except Exception as e:
            logger.error(f"Error creando incentivo para {user.username} en {zone.name}: {e}")
            return None
    
    @staticmethod
    def _generate_description(rule, zone, conditions):
        """Genera una descripción personalizada para el incentivo"""
        base_descriptions = {
            IncentiveType.HIGH_DEMAND: f"¡Alta demanda en {zone.name}! Incentivo por publicar tu propiedad en esta zona popular.",
            IncentiveType.LOW_SUPPLY: f"Pocas opciones en {zone.name}. Te ayudamos a encontrar tu hogar ideal con este incentivo.",
            IncentiveType.MARKET_BALANCE: f"Incentivo de equilibrio de mercado para {zone.name}.",
            IncentiveType.ZONE_PROMOTION: f"¡Descubre las oportunidades en {zone.name}! Incentivo promocional especial."
        }
        
        description = base_descriptions.get(rule.incentive_type, rule.description)
        
        # Agregar información contextual
        if conditions['offer_demand_ratio'] < 0.3:
            description += " Zona con muy alta demanda."
        elif conditions['offer_demand_ratio'] > 3.0:
            description += " Excelente momento para encontrar opciones."
            
        return description
    
    @staticmethod
    def process_zone_activity_update(zone):
        """Procesa actualizaciones de actividad en una zona y genera incentivos si es necesario"""
        conditions = IncentiveService.analyze_zone_market_conditions(zone)
        
        # Verificar si se necesitan incentivos inmediatos
        urgent_conditions = [
            conditions['high_demand'] and conditions['offer_demand_ratio'] < 0.2,
            conditions['low_supply'] and zone.demand_count > 15,
            conditions['low_activity'] and zone.avg_price > 0
        ]
        
        if any(urgent_conditions):
            logger.info(f"Condiciones urgentes detectadas en {zone.name}, generando incentivos...")
            return IncentiveService.generate_automatic_incentives_for_zone(zone)
        
        return []
    
    @staticmethod
    def generate_automatic_incentives_for_zone(zone):
        """Genera incentivos automáticos para una zona específica"""
        generated_incentives = []
        conditions = IncentiveService.analyze_zone_market_conditions(zone)
        
        # Obtener reglas aplicables
        active_rules = IncentiveRule.objects.filter(is_active=True)
        
        for rule in active_rules:
            if rule.check_conditions(zone) and not IncentiveService._is_in_cooldown(rule, zone):
                eligible_users = IncentiveService._get_eligible_users(zone, rule.incentive_type)
                
                for user in eligible_users:
                    incentive = IncentiveService._create_incentive(user, zone, rule, conditions)
                    if incentive:
                        generated_incentives.append(incentive)
        
        return generated_incentives
    
    @staticmethod
    def get_user_active_incentives(user):
        """Obtiene los incentivos activos de un usuario"""
        return Incentive.objects.filter(
            user=user,
            is_active=True,
            valid_until__gt=timezone.now()
        ).select_related('zone')
    
    @staticmethod
    def expire_old_incentives():
        """Marca como inactivos los incentivos expirados"""
        expired_count = Incentive.objects.filter(
            is_active=True,
            valid_until__lt=timezone.now()
        ).update(is_active=False)
        
        logger.info(f"Se marcaron como inactivos {expired_count} incentivos expirados")
        return expired_count