from rest_framework import serializers
from .models import Incentive, IncentiveRule
from zone.models import Zone
from django.contrib.auth.models import User


class IncentiveSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    effectiveness_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Incentive
        fields = [
            'id', 'user', 'user_username', 'zone', 'zone_name', 
            'incentive_type', 'amount', 'description', 'is_active',
            'valid_until', 'offer_demand_ratio', 'zone_activity_score',
            'created_at', 'updated_at', 'is_expired', 'effectiveness_score'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'user_username', 
            'zone_name', 'is_expired', 'effectiveness_score'
        ]
    
    def get_effectiveness_score(self, obj):
        """Calcular el puntaje de efectividad del incentivo"""
        try:
            return obj.calculate_effectiveness()
        except:
            return 0.0


class IncentiveRuleSerializer(serializers.ModelSerializer):
    active_incentives_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IncentiveRule
        fields = [
            'id', 'name', 'description', 'is_active',
            'min_offer_count', 'max_offer_count', 
            'min_demand_count', 'max_demand_count',
            'min_offer_demand_ratio', 'max_offer_demand_ratio',
            'incentive_type', 'base_amount', 'max_amount',
            'cooldown_hours', 'max_per_user_per_day',
            'created_at', 'updated_at', 'active_incentives_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'active_incentives_count']
    
    def get_active_incentives_count(self, obj):
        """Contar incentivos activos generados por esta regla"""
        return Incentive.objects.filter(
            description__icontains=obj.name,
            is_active=True
        ).count()


class ZoneMarketAnalysisSerializer(serializers.Serializer):
    """Serializer para análisis de mercado de zonas"""
    zone_id = serializers.IntegerField()
    zone_name = serializers.CharField()
    offer_count = serializers.IntegerField()
    demand_count = serializers.IntegerField()
    offer_demand_ratio = serializers.FloatField()
    activity_score = serializers.FloatField()
    market_condition = serializers.CharField()
    eligible_rules = serializers.ListField(child=serializers.CharField())
    recommended_incentive_type = serializers.CharField()
    
    
class IncentiveGenerationRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de generación de incentivos"""
    zone_id = serializers.IntegerField(required=False)
    dry_run = serializers.BooleanField(default=False)
    force_generation = serializers.BooleanField(default=False)