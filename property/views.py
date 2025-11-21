from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.db.models import Q, Count, Avg
from .models import Property, PropertyView, PropertyViewEvent
from .serializers import (
    PropertySerializer, PropertyGeoSerializer, PropertyCreateSerializer,
    PropertyMapSerializer, PropertySearchSerializer, RoomieSeekerPropertySerializer
)
from zone.models import Zone
from bk_habitto.mixins import MessageConfigMixin
from matching.models import SearchProfile
from utils.matching import calculate_property_match_score, create_property_matches_for_profile
from django.conf import settings

class PropertyViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar propiedades con funcionalidades GIS y filtros por zona.
    Personaliza la respuesta según el tipo de usuario (inquilino, propietario, agente).
    """
    queryset = Property.objects.select_related('zone', 'owner').prefetch_related('amenities', 'accepted_payment_methods')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active', 'owner', 'zone', 'bedrooms', 'bathrooms']
    search_fields = ['address', 'description', 'zone__name']
    ordering_fields = ['price', 'created_at', 'size']
    permission_classes = [IsAuthenticatedOrReadOnly]
    success_messages = {
        'list': 'Propiedades obtenidas exitosamente',
        'retrieve': 'Propiedad obtenida exitosamente',
        'create': 'Propiedad creada exitosamente',
        'update': 'Propiedad actualizada exitosamente',
        'partial_update': 'Propiedad actualizada exitosamente',
        'destroy': 'Propiedad eliminada exitosamente',
    }

    def get_serializer_class(self):
        """Selecciona el serializer apropiado según la acción."""
        if self.action == 'create':
            return PropertyCreateSerializer
        elif self.action == 'map':
            return PropertyMapSerializer
        elif self.action == 'geojson':
            return PropertyGeoSerializer
        return PropertySerializer

    def get_queryset(self):
        """
        Personaliza el queryset según el tipo de usuario:
        - Inquilino: Solo propiedades activas
        - Propietario: Sus propias propiedades + activas de otros
        - Agente: Propiedades asignadas + activas
        """
        queryset = self.queryset.order_by('-created_at')
        
        if not self.request.user.is_authenticated:
            # Usuarios anónimos solo ven propiedades activas
            return queryset.filter(is_active=True)
        
        user_type = getattr(self.request.user, 'user_type', 'inquilino')
        
        if user_type == 'inquilino':
            # Inquilinos solo ven propiedades activas
            queryset = queryset.filter(is_active=True)
        elif user_type == 'propietario':
            # Propietarios ven sus propiedades + activas de otros
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(is_active=True)
            )
        elif user_type == 'agente':
            # Agentes ven propiedades asignadas + activas
            # Asumiendo que hay un campo 'agent' en Property o relación similar
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(is_active=True)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Override list to include roomie seekers when requested.
        """
        include_roomies = request.query_params.get('include_roomies', 'false').lower() == 'true'
        
        if include_roomies:
            # Get regular properties
            properties = self.filter_queryset(self.get_queryset())
            
            # Get roomie seekers
            roomie_seekers = SearchProfile.objects.filter(
                roommate_preference__in=['looking', 'open']
            ).select_related('user').prefetch_related('preferred_zones')
            
            # Serialize both
            properties_serializer = self.get_serializer(properties, many=True)
            roomie_serializer = RoomieSeekerPropertySerializer(roomie_seekers, many=True, context=self.get_serializer_context())
            
            # Combine results
            combined_data = properties_serializer.data + roomie_serializer.data
            
            # Sort by created_at or other criteria (handle mixed types)
            def get_sort_key(item):
                created_at = item.get('created_at', '')
                if created_at:
                    # Convert to string for consistent comparison
                    return str(created_at)
                return ''
            
            combined_data.sort(key=get_sort_key, reverse=True)
            
            return Response(combined_data)
        else:
            return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Asigna el propietario automáticamente al crear una propiedad."""
        prop = serializer.save(owner=self.request.user)
        # Trigger de matches automáticos con perfiles cercanos
        try:
            # Buscar perfiles con ubicación definida cerca de la propiedad
            profiles = SearchProfile.objects.all()
            for profile in profiles[:500]:
                score, meta = calculate_property_match_score(profile, prop)
                from matching.models import Match
                threshold = getattr(settings, 'MATCH_MIN_SCORE', 70)
                if score >= threshold:
                    Match.objects.update_or_create(
                        match_type='property',
                        subject_id=prop.id,
                        target_user=profile.user,
                        defaults={'score': score, 'metadata': meta}
                    )
        except Exception:
            pass

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        resp = super().retrieve(request, *args, **kwargs)
        try:
            if request.user.is_authenticated:
                pv, _ = PropertyView.objects.get_or_create(user=request.user, property=obj)
                pv.count = (pv.count or 0) + 1
                pv.save(update_fields=['count', 'last_viewed'])
                PropertyViewEvent.objects.create(user=request.user, property=obj)
        except Exception:
            pass
        return resp

    def list(self, request, *args, **kwargs):
        """
        Override list to include roomie seekers when requested, and handle match scoring.
        """
        include_roomies = request.query_params.get('include_roomies', 'false').lower() == 'true'
        min_score = request.query_params.get('match_score')
        order_by_match = request.query_params.get('order_by_match') in ['1', 'true', 'True']
        
        if min_score and request.user.is_authenticated:
            try:
                min_score = float(min_score)
            except ValueError:
                min_score = None
        else:
            min_score = None
        
        if include_roomies:
            # Get regular properties
            properties = self.filter_queryset(self.get_queryset())
            
            # Get roomie seekers
            roomie_seekers = SearchProfile.objects.filter(
                roommate_preference__in=['looking', 'open']
            ).select_related('user').prefetch_related('preferred_zones')
            
            # Serialize both
            properties_serializer = self.get_serializer(properties, many=True)
            roomie_serializer = RoomieSeekerPropertySerializer(roomie_seekers, many=True, context=self.get_serializer_context())
            
            # Combine results
            combined_data = properties_serializer.data + roomie_serializer.data
            
            # Sort by created_at or other criteria (handle mixed types)
            def get_sort_key(item):
                created_at = item.get('created_at', '')
                if created_at:
                    # Convert to string for consistent comparison
                    return str(created_at)
                return ''
            
            combined_data.sort(key=get_sort_key, reverse=True)
            
            return Response(combined_data)
        else:
            response = super().list(request, *args, **kwargs)
            if (min_score is not None or order_by_match) and request.user.is_authenticated:
                profile = SearchProfile.objects.filter(user=request.user).first()
                if not profile:
                    return response
                results = response.data.get('results') if isinstance(response.data, dict) else response.data
                processed = []
                # results puede ser lista de dicts de propiedades serializadas
                from property.models import Property as PropertyModel
                id_key = 'id'
                for item in results:
                    try:
                        prop_id = item.get(id_key)
                        prop_obj = PropertyModel.objects.get(id=prop_id)
                        score, _ = calculate_property_match_score(profile, prop_obj)
                        item['_match_score'] = score
                        if (min_score is None) or (score >= min_score):
                            processed.append(item)
                    except Exception:
                        processed.append(item)
                if order_by_match:
                    processed.sort(key=lambda x: x.get('_match_score', 0), reverse=True)
                if isinstance(response.data, dict):
                    response.data['results'] = processed
                    response.data['count'] = len(processed)
                else:
                    response.data = processed
            return response
    
    @action(detail=True, methods=['post'], url_path='convert-to-roomie')
    def convert_to_roomie_listing(self, request, pk=None):
        """
        Convierte una propiedad en una publicación de búsqueda de roomie.
        Se usa cuando un inquilino da like a una propiedad y el propietario acepta.
        """
        property_obj = self.get_object()
        
        # Verificar que el usuario sea el propietario o tenga permisos
        if property_obj.owner != request.user:
            return Response(
                {'error': 'No tiene permisos para convertir esta propiedad'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar que la propiedad permite roomies
        if not property_obj.allows_roommates:
            return Response(
                {'error': 'Esta propiedad no permite roomies'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener el perfil del inquilino que dio like (debe estar en el request)
        tenant_profile_id = request.data.get('tenant_profile_id')
        if not tenant_profile_id:
            return Response(
                {'error': 'Se requiere tenant_profile_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant_profile = SearchProfile.objects.get(id=tenant_profile_id)
        except SearchProfile.DoesNotExist:
            return Response(
                {'error': 'Perfil de inquilino no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Marcar la propiedad como roomie listing
        property_obj.is_roomie_listing = True
        property_obj.roomie_profile = tenant_profile
        property_obj.save()
        
        # Serializar la propiedad actualizada
        serializer = self.get_serializer(property_obj)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Propiedad convertida a búsqueda de roomie exitosamente')
        return resp

    @action(detail=False, methods=['get'], url_path='map')
    def map(self, request):
        """
        Endpoint optimizado para mostrar propiedades en el mapa.
        Soporta filtros por zona, ubicación y radio de búsqueda.
        
        Parámetros:
        - zone_id: ID de la zona
        - lat, lng, radius: Búsqueda por ubicación y radio (en km)
        - price_min, price_max: Rango de precios
        """
        queryset = self.get_queryset().filter(is_active=True)
        
        # Filtro por zona
        zone_id = request.query_params.get('zone_id')
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        
        # Filtro por ubicación y radio
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', '5')  # Default 5km
        
        if lat and lng:
            try:
                point = Point(float(lng), float(lat), srid=4326)
                distance = Distance(km=float(radius))
                queryset = queryset.filter(location__distance_lte=(point, distance))
                # Ordenar por distancia
                queryset = queryset.annotate(
                    distance=DistanceFunction('location', point)
                ).order_by('distance')
            except (ValueError, TypeError):
                pass
        
        # Filtros adicionales
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        
        property_type = request.query_params.get('type')
        if property_type:
            queryset = queryset.filter(type=property_type)
        
        # Limitar resultados para rendimiento del mapa
        queryset = queryset[:200]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'type': 'FeatureCollection',
            'features': serializer.data,
            'count': len(serializer.data)
        })

    @action(detail=False, methods=['get'], url_path='geojson')
    def geojson(self, request):
        """
        Devuelve propiedades en formato GeoJSON completo para visualización avanzada.
        """
        queryset = self.get_queryset().filter(is_active=True)
        
        # Aplicar filtros básicos
        zone_id = request.query_params.get('zone_id')
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        
        serializer = PropertyGeoSerializer(queryset[:100], many=True)  # Limitar para rendimiento
        return Response({
            'type': 'FeatureCollection',
            'features': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='search')
    def search(self, request):
        """
        Búsqueda avanzada de propiedades con logging para estadísticas de demanda.
        """
        serializer = PropertySearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        search_data = serializer.validated_data
        queryset = self.get_queryset().filter(is_active=True)
        
        # Aplicar filtros de búsqueda
        if search_data.get('zone_id'):
            queryset = queryset.filter(zone_id=search_data['zone_id'])
            
            # Registrar búsqueda en la zona para estadísticas de demanda
            try:
                zone = Zone.objects.get(id=search_data['zone_id'])
                zone.demand_count += 1
                zone.save(update_fields=['demand_count'])
            except Zone.DoesNotExist:
                pass
        
        if search_data.get('price_min'):
            queryset = queryset.filter(price__gte=search_data['price_min'])
        if search_data.get('price_max'):
            queryset = queryset.filter(price__lte=search_data['price_max'])
        
        if search_data.get('property_type'):
            queryset = queryset.filter(type=search_data['property_type'])
        
        if search_data.get('bedrooms'):
            queryset = queryset.filter(bedrooms=search_data['bedrooms'])
        if search_data.get('bathrooms'):
            queryset = queryset.filter(bathrooms=search_data['bathrooms'])
        
        # Búsqueda por ubicación y radio
        if search_data.get('latitude') and search_data.get('longitude'):
            point = Point(search_data['longitude'], search_data['latitude'], srid=4326)
            radius = search_data.get('radius', 5)  # Default 5km
            distance = Distance(km=radius)
            queryset = queryset.filter(location__distance_lte=(point, distance))
            queryset = queryset.annotate(
                distance=DistanceFunction('location', point)
            ).order_by('distance')
        
        # Búsqueda por texto
        if search_data.get('search_text'):
            queryset = queryset.filter(
                Q(address__icontains=search_data['search_text']) |
                Q(description__icontains=search_data['search_text']) |
                Q(zone__name__icontains=search_data['search_text'])
            )
        
        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PropertySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PropertySerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='nearby')
    def nearby(self, request, pk=None):
        """
        Encuentra propiedades cercanas a una propiedad específica.
        """
        property_obj = self.get_object()
        if not property_obj.location:
            return Response(
                {'error': 'La propiedad no tiene ubicación definida'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        radius = float(request.query_params.get('radius', '2'))  # Default 2km
        nearby_properties = property_obj.get_nearby_properties(distance_km=radius)
        
        # Excluir la propiedad actual
        nearby_properties = nearby_properties.exclude(id=property_obj.id)
        
        serializer = PropertySerializer(nearby_properties[:20], many=True, context={'request': request})
        return Response({
            'count': nearby_properties.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Estadísticas generales de propiedades, personalizadas por tipo de usuario.
        """
        queryset = self.get_queryset()
        
        # Estadísticas básicas
        total_properties = queryset.count()
        active_properties = queryset.filter(is_active=True).count()
        avg_price = queryset.filter(is_active=True).aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0
        
        # Estadísticas por zona
        zone_stats = Zone.objects.annotate(
            property_count=Count('property', filter=Q(property__is_active=True))
        ).values('id', 'name', 'property_count', 'avg_price', 'offer_count', 'demand_count')
        
        user_type = getattr(request.user, 'user_type', 'inquilino') if request.user.is_authenticated else 'inquilino'
        
        response_data = {
            'total_properties': total_properties,
            'active_properties': active_properties,
            'avg_price': round(float(avg_price), 2),
            'zones': list(zone_stats)
        }
        
        # Información adicional según tipo de usuario
        if user_type == 'propietario':
            user_properties = queryset.filter(owner=request.user).count() if request.user.is_authenticated else 0
            response_data['user_properties'] = user_properties
        elif user_type == 'agente':
            # Estadísticas para agentes (leads, propiedades gestionadas, etc.)
            response_data['leads_count'] = sum(zone['demand_count'] for zone in zone_stats)
        
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='seen', permission_classes=[IsAuthenticated])
    def seen(self, request):
        """
        Lista de propiedades con las que el usuario ya interactuó (aceptadas, rechazadas o con feedback).
        """
        from matching.models import Match
        qs = Match.objects.filter(target_user=request.user, match_type='property')
        property_ids = list(qs.values_list('subject_id', flat=True))
        return Response({'count': len(property_ids), 'property_ids': property_ids})

    @action(detail=True, methods=['post'], url_path='view', permission_classes=[IsAuthenticated])
    def view(self, request, pk=None):
        obj = self.get_object()
        pv, _ = PropertyView.objects.get_or_create(user=request.user, property=obj)
        pv.count = (pv.count or 0) + 1
        pv.save(update_fields=['count', 'last_viewed'])
        PropertyViewEvent.objects.create(user=request.user, property=obj)
        return Response({'status': 'ok', 'property_id': obj.id, 'count': pv.count})

    @action(detail=False, methods=['get'], url_path='views', permission_classes=[IsAuthenticated])
    def views(self, request):
        qs = PropertyView.objects.filter(user=request.user).select_related('property').order_by('-last_viewed')
        data = [{'property_id': v.property_id, 'count': v.count, 'last_viewed': v.last_viewed} for v in qs]
        return Response({'count': qs.count(), 'results': data})

    @action(detail=True, methods=['post'], url_path='like', permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        obj = self.get_object()
        profile = SearchProfile.objects.filter(user=request.user).first()
        from matching.models import Match, MatchFeedback
        # Calcular score y crear/actualizar match independientemente del umbral
        try:
            score, meta = calculate_property_match_score(profile, obj) if profile else (0, {})
        except Exception:
            score, meta = (0, {})
        match, _ = Match.objects.update_or_create(
            match_type='property', subject_id=obj.id, target_user=request.user,
            defaults={'score': score, 'metadata': meta, 'status': 'pending'}
        )
        MatchFeedback.objects.create(match=match, user=request.user, feedback_type='like', reason=request.data.get('reason'))
        
        # Notificación y conversación con propietario
        try:
            from notification.models import Notification
            from message.models import Message
            Message.objects.create(sender=request.user, receiver=obj.owner, content=f"Interesado en tu propiedad (match {score}%).")
            Notification.objects.create(user=obj.owner, message=f"{request.user.username} indicó interés en tu propiedad (score {score}%).")
            
            # Enviar notificación WebSocket en tiempo real
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from message.notification_consumers import send_property_like_notification
            
            # Preparar datos del usuario interesado
            interested_user_data = {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
            
            # Obtener información del perfil si existe
            try:
                user_profile = request.user.userprofile
                interested_user_data.update({
                    'phone': getattr(user_profile, 'phone', ''),
                    'user_type': getattr(user_profile, 'user_type', 'inquilino')
                })
            except:
                pass
            
            # Enviar notificación asíncrona
            channel_layer = get_channel_layer()
            async_to_sync(send_property_like_notification)(
                channel_layer,
                obj.owner.id,
                obj.id,
                f"{obj.type} en {obj.address}",
                interested_user_data
            )
            
        except Exception as e:
            # Log del error pero no interrumpir la respuesta
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar notificación WebSocket: {e}")
            pass
            
        return Response({'status': match.status, 'match_id': match.id, 'score': score})

    @action(detail=True, methods=['post'], url_path='reject', permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        obj = self.get_object()
        profile = SearchProfile.objects.filter(user=request.user).first()
        from matching.models import Match, MatchFeedback
        try:
            score, meta = calculate_property_match_score(profile, obj) if profile else (0, {})
        except Exception:
            score, meta = (0, {})
        match, _ = Match.objects.update_or_create(
            match_type='property', subject_id=obj.id, target_user=request.user,
            defaults={'score': score, 'metadata': meta}
        )
        match.status = 'rejected'
        match.save(update_fields=['status', 'updated_at'])
        MatchFeedback.objects.create(match=match, user=request.user, feedback_type='dislike', reason=request.data.get('reason'))
        return Response({'status': 'rejected', 'match_id': match.id})
