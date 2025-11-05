from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.db.models import Q, Count, Avg, F
from .models import Zone, ZoneSearchLog
from .serializers import (
    ZoneSerializer, ZoneGeoSerializer, ZoneStatsSerializer, 
    ZoneHeatmapSerializer, ZoneSearchLogSerializer, ZoneCreateSerializer
)
from bk_habitto.mixins import MessageConfigMixin
from matching.models import Match, RoommateRequest


class ZoneViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de zonas con funcionalidades GIS y estadísticas.
    
    Endpoints disponibles:
    - GET /api/zones/ - Lista todas las zonas
    - POST /api/zones/ - Crear nueva zona (solo admin)
    - GET /api/zones/{id}/ - Detalle de zona específica
    - PUT/PATCH /api/zones/{id}/ - Actualizar zona (solo admin)
    - DELETE /api/zones/{id}/ - Eliminar zona (solo admin)
    - GET /api/zones/stats/ - Estadísticas de todas las zonas
    - GET /api/zones/{id}/stats/ - Estadísticas de zona específica
    - GET /api/zones/heatmap/ - Datos para heatmap
    - GET /api/zones/geojson/ - Todas las zonas en formato GeoJSON
    - POST /api/zones/search_log/ - Registrar búsqueda por zona
    """
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    success_messages = {
        'list': 'Zonas obtenidas exitosamente',
        'retrieve': 'Zona obtenida exitosamente',
        'create': 'Zona creada exitosamente',
        'update': 'Zona actualizada exitosamente',
        'partial_update': 'Zona actualizada exitosamente',
        'destroy': 'Zona eliminada exitosamente',
        'stats': 'Estadísticas de zonas obtenidas exitosamente',
        'zone_stats': 'Estadísticas de zona obtenidas exitosamente',
        'heatmap': 'Datos de mapa de calor obtenidos exitosamente',
        'geojson': 'Datos GeoJSON obtenidos exitosamente',
        'search_log': 'Búsqueda registrada exitosamente',
        'nearby_zones': 'Zonas cercanas obtenidas exitosamente',
        'find_by_location': 'Zona encontrada exitosamente',
    }
    
    def get_permissions(self):
        """
        Permisos personalizados según la acción.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Solo admin puede crear/modificar/eliminar zonas
            permission_classes = [IsAuthenticated]  # Aquí podrías agregar IsAdminUser
        else:
            # Lectura pública para stats y visualizaciones
            permission_classes = [AllowAny]
        
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'create':
            return ZoneCreateSerializer
        elif self.action == 'geojson':
            return ZoneGeoSerializer
        elif self.action in ['stats', 'zone_stats']:
            return ZoneStatsSerializer
        elif self.action == 'heatmap':
            return ZoneHeatmapSerializer
        return ZoneSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Endpoint: GET /api/zones/stats/
        
        Retorna estadísticas generales de todas las zonas.
        Útil para propietarios y agentes para ver el panorama general.
        """
        zones = self.get_queryset()
        
        # Filtros opcionales
        user_type = request.query_params.get('user_type')
        
        # Personalización según tipo de usuario
        if user_type == 'propietario':
            # Propietarios ven solo estadísticas agregadas para incentivar equilibrio
            stats_data = {
                'total_zones': zones.count(),
                'avg_price_all_zones': zones.aggregate(avg=Avg('avg_price'))['avg'],
                'high_demand_zones': zones.filter(
                    demand_count__gt=F('offer_count')
                ).count(),
                'opportunities': zones.filter(
                    demand_count__gt=F('offer_count'),
                    offer_count__lt=5
                ).values('id', 'name', 'demand_count', 'offer_count')[:5]
            }
            resp = Response(stats_data)
            self.set_response_message(resp, 'Estadísticas de zonas obtenidas exitosamente')
            return resp
        
        elif user_type == 'agente':
            # Agentes ven leads y estadísticas detalladas
            serializer = self.get_serializer(zones, many=True)
            resp = Response({
                'zones': serializer.data,
                'total_leads': ZoneSearchLog.objects.count(),
                'recent_searches': ZoneSearchLog.objects.select_related('zone')
                    .order_by('-created_at')[:10]
                    .values('zone__name', 'search_params', 'created_at')
            })
            self.set_response_message(resp, 'Estadísticas de zonas obtenidas exitosamente')
            return resp
        
        else:
            # Inquilinos y usuarios generales ven estadísticas básicas
            serializer = self.get_serializer(zones, many=True)
            resp = Response(serializer.data)
            self.set_response_message(resp, 'Estadísticas de zonas obtenidas exitosamente')
            return resp

    @action(detail=True, methods=['get'])
    def zone_stats(self, request, pk=None):
        """
        Endpoint: GET /api/zones/{id}/stats/
        
        Retorna estadísticas detalladas de una zona específica.
        """
        zone = self.get_object()
        serializer = self.get_serializer(zone)
        
        # Información adicional según tipo de usuario
        user_type = request.query_params.get('user_type')
        response_data = serializer.data

        # Métricas de matching
        try:
            # Matches sobre propiedades de la zona
            from property.models import Property
            prop_ids = list(Property.objects.filter(zone=zone).values_list('id', flat=True))
            total_matches = Match.objects.filter(match_type='property', subject_id__in=prop_ids).count()
            accepted_matches = Match.objects.filter(match_type='property', subject_id__in=prop_ids, status='accepted').count()
            match_ratio = (accepted_matches / total_matches) if total_matches > 0 else 0
            # Roomie demand: solicitudes cuyo creador prefiere esta zona
            roomie_demand = RoommateRequest.objects.filter(creator__preferred_zones=zone, is_active=True).count()
        except Exception:
            match_ratio = 0
            roomie_demand = 0
        response_data['match_ratio'] = round(float(match_ratio), 3)
        response_data['roomie_demand'] = roomie_demand
        
        if user_type == 'propietario':
            # Información específica para propietarios
            response_data['incentives_available'] = zone.offer_count < zone.demand_count
            response_data['competition_level'] = 'Baja' if zone.offer_count < 10 else 'Alta'
            
        elif user_type == 'agente':
            # Información específica para agentes
            recent_searches = ZoneSearchLog.objects.filter(zone=zone)\
                .order_by('-created_at')[:5]\
                .values('search_params', 'created_at', 'user__username')
            response_data['recent_searches'] = list(recent_searches)
            
        resp = Response(response_data)
        self.set_response_message(resp, 'Estadísticas de zona obtenidas exitosamente')
        return resp

    @action(detail=False, methods=['get'])
    def heatmap(self, request):
        """
        Endpoint: GET /api/zones/heatmap/
        
        Retorna datos optimizados para generar heatmap de oferta/demanda.
        
        Ejemplo de respuesta:
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": 1,
                        "name": "Centro",
                        "intensity": 0.8,
                        "demand_count": 25,
                        "offer_count": 5
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-63.1821, -17.7834]
                    }
                }
            ]
        }
        """
        zones = self.get_queryset()
        serializer = self.get_serializer(zones, many=True)
        
        # Convertir a formato GeoJSON para heatmap
        features = []
        for zone_data in serializer.data:
            if zone_data['center_lat'] and zone_data['center_lng']:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": zone_data['id'],
                        "name": zone_data['name'],
                        "intensity": zone_data['intensity']
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [zone_data['center_lng'], zone_data['center_lat']]
                    }
                }
                features.append(feature)
        
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }
        
        resp = Response(geojson_data)
        self.set_response_message(resp, 'Datos de mapa de calor obtenidos exitosamente')
        return resp

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """
        Endpoint: GET /api/zones/geojson/
        
        Retorna todas las zonas en formato GeoJSON completo con bounds.
        Útil para visualizar límites de zonas en mapas.
        """
        zones = self.get_queryset()
        serializer = self.get_serializer(zones, many=True)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Datos GeoJSON obtenidos exitosamente')
        return resp

    @action(detail=False, methods=['post'])
    def search_log(self, request):
        """
        Endpoint: POST /api/zones/search_log/
        
        Registra una búsqueda por zona para actualizar estadísticas de demanda.
        
        Body:
        {
            "zone": 1,
            "search_params": {
                "type": "departamento",
                "min_price": 3000,
                "max_price": 5000
            }
        }
        """
        serializer = ZoneSearchLogSerializer(data=request.data)
        if serializer.is_valid():
            # Asignar usuario si está autenticado
            if request.user.is_authenticated:
                serializer.save(user=request.user)
            else:
                serializer.save()
            
            resp = Response(serializer.data, status=status.HTTP_201_CREATED)
            self.set_response_message(resp, 'Búsqueda registrada exitosamente')
            return resp
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def nearby_zones(self, request, pk=None):
        """
        Endpoint: GET /api/zones/{id}/nearby_zones/
        
        Retorna zonas cercanas a la zona especificada.
        """
        zone = self.get_object()
        nearby = zone.get_nearby_zones()
        serializer = ZoneSerializer(nearby, many=True)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Zonas cercanas obtenidas exitosamente')
        return resp

    @action(detail=False, methods=['get'])
    def find_by_location(self, request):
        """
        Endpoint: GET /api/zones/find_by_location/?lat=-17.7834&lng=-63.1821
        
        Encuentra la zona que contiene las coordenadas especificadas.
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'Parámetros lat y lng son requeridos'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            point = Point(float(lng), float(lat))
            zone = Zone.objects.filter(bounds__contains=point).first()
            
            if zone:
                serializer = ZoneSerializer(zone)
                return Response(serializer.data)
            else:
                return Response(
                    {'message': 'No se encontró zona para estas coordenadas'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Coordenadas inválidas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
