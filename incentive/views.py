from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Incentive, IncentiveRule
from .serializers import IncentiveSerializer, IncentiveRuleSerializer
from .services import IncentiveService
from zone.models import Zone
import logging
from bk_habitto.mixins import MessageConfigMixin

logger = logging.getLogger(__name__)


class IncentiveViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    """ViewSet para gestionar incentivos de usuarios"""
    serializer_class = IncentiveSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Incentivos obtenidos exitosamente',
        'retrieve': 'Incentivo obtenido exitosamente',
        'create': 'Incentivo creado exitosamente',
        'update': 'Incentivo actualizado exitosamente',
        'partial_update': 'Incentivo actualizado exitosamente',
        'destroy': 'Incentivo eliminado exitosamente',
        'active': 'Incentivos activos obtenidos exitosamente',
        'by_zone': 'Incentivos por zona obtenidos exitosamente',
        'use': 'Incentivo usado exitosamente',
    }
    
    def get_queryset(self):
        """Filtrar incentivos por usuario autenticado"""
        return Incentive.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Asignar el usuario autenticado al crear un incentivo"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtener incentivos activos del usuario"""
        active_incentives = IncentiveService.get_user_active_incentives(request.user)
        serializer = self.get_serializer(active_incentives, many=True)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Incentivos activos obtenidos exitosamente')
        return resp
    
    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        """Obtener incentivos del usuario filtrados por zona"""
        zone_id = request.query_params.get('zone_id')
        if not zone_id:
            return Response(
                {'error': 'zone_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            zone = Zone.objects.get(id=zone_id)
            incentives = self.get_queryset().filter(zone=zone)
            serializer = self.get_serializer(incentives, many=True)
            resp = Response(serializer.data)
            self.set_response_message(resp, 'Incentivos por zona obtenidos exitosamente')
            return resp
        except Zone.DoesNotExist:
            return Response(
                {'error': 'Zone not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Marcar un incentivo como usado"""
        incentive = self.get_object()
        
        if not incentive.is_active:
            return Response(
                {'error': 'Incentive is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if incentive.is_expired:
            return Response(
                {'error': 'Incentive has expired'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marcar como usado (inactivo)
        incentive.is_active = False
        incentive.save()
        
        logger.info(f"Incentive {incentive.id} used by user {request.user.username}")
        
        resp = Response({
            'message': 'Incentive used successfully',
            'incentive': self.get_serializer(incentive).data
        })
        self.set_response_message(resp, 'Incentivo usado exitosamente')
        return resp


class IncentiveRuleViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    """ViewSet para gestionar reglas de incentivos (solo admin)"""
    queryset = IncentiveRule.objects.all().order_by('name')
    serializer_class = IncentiveRuleSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Reglas de incentivos obtenidas exitosamente',
        'retrieve': 'Regla de incentivo obtenida exitosamente',
        'create': 'Regla de incentivo creada exitosamente',
        'update': 'Regla de incentivo actualizada exitosamente',
        'partial_update': 'Regla de incentivo actualizada exitosamente',
        'destroy': 'Regla de incentivo eliminada exitosamente',
        'generate_incentives': 'Incentivos generados exitosamente',
        'market_analysis': 'Análisis de mercado obtenido exitosamente',
        'toggle_active': 'Regla activada exitosamente',
    }
    
    def get_permissions(self):
        """Solo administradores pueden crear, actualizar o eliminar reglas"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
            # Verificar si es admin en el método
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        """Solo administradores pueden crear reglas"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can create incentive rules'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Solo administradores pueden actualizar reglas"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can update incentive rules'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Solo administradores pueden eliminar reglas"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can delete incentive rules'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def generate_incentives(self, request):
        """Generar incentivos automáticos manualmente (solo admin)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can generate incentives'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            zone_id = request.data.get('zone_id')
            
            if zone_id:
                # Generar para una zona específica
                try:
                    zone = Zone.objects.get(id=zone_id)
                    incentives = IncentiveService.generate_automatic_incentives_for_zone(zone)
                    message = f'Generated {len(incentives)} incentives for {zone.name}'
                except Zone.DoesNotExist:
                    return Response(
                        {'error': 'Zone not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Generar para todas las zonas
                incentives = IncentiveService.generate_automatic_incentives()
                message = f'Generated {len(incentives)} incentives for all zones'
            
            logger.info(f"Manual incentive generation by {request.user.username}: {message}")
            
            resp = Response({
                'message': message,
                'incentives_count': len(incentives),
                'timestamp': timezone.now()
            })
            # Ajustar mensaje según si es por zona o todas
            if zone_id:
                self.set_response_message(resp, 'Incentivos generados exitosamente')
            else:
                self.set_response_message(resp, 'Incentivos generados exitosamente')
            return resp
            
        except Exception as e:
            logger.error(f"Error generating incentives: {e}")
            return Response(
                {'error': f'Error generating incentives: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def market_analysis(self, request):
        """Obtener análisis de mercado para todas las zonas"""
        zone_id = request.query_params.get('zone_id')
        
        if zone_id:
            # Análisis para una zona específica
            try:
                zone = Zone.objects.get(id=zone_id)
                conditions = IncentiveService.analyze_zone_market_conditions(zone)
                resp = Response({
                    'zone': {
                        'id': zone.id,
                        'name': zone.name,
                        'offer_count': zone.offer_count,
                        'demand_count': zone.demand_count
                    },
                    'conditions': conditions,
                    'timestamp': timezone.now()
                })
                self.set_response_message(resp, 'Análisis de mercado obtenido exitosamente')
                return resp
            except Zone.DoesNotExist:
                return Response(
                    {'error': 'Zone not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Análisis para todas las zonas
            zones_analysis = []
            for zone in Zone.objects.all():
                conditions = IncentiveService.analyze_zone_market_conditions(zone)
                zones_analysis.append({
                    'zone': {
                        'id': zone.id,
                        'name': zone.name,
                        'offer_count': zone.offer_count,
                        'demand_count': zone.demand_count
                    },
                    'conditions': conditions
                })
            
            resp = Response({
                'zones_analysis': zones_analysis,
                'timestamp': timezone.now()
            })
            self.set_response_message(resp, 'Análisis de mercado para todas las zonas obtenido exitosamente')
            return resp
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activar/desactivar una regla de incentivo (solo admin)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can toggle incentive rules'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        
        status_text = 'activated' if rule.is_active else 'deactivated'
        logger.info(f"Incentive rule {rule.name} {status_text} by {request.user.username}")
        
        resp = Response({
            'message': f'Rule {status_text} successfully',
            'rule': self.get_serializer(rule).data
        })
        # Mensaje condicional según estado
        toggle_message = 'Regla activada exitosamente' if rule.is_active else 'Regla desactivada exitosamente'
        self.set_response_message(resp, toggle_message)
        return resp
