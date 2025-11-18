from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import F, Q
from django.contrib.auth.models import User
from .models import SearchProfile, RoommateRequest, Match, MatchFeedback
from .serializers import (
    SearchProfileSerializer, RoommateRequestSerializer, MatchSerializer, MatchFeedbackSerializer
)
from bk_habitto.mixins import MessageConfigMixin
from utils.matching import (
    calculate_property_match_score, calculate_roommate_match_score, calculate_agent_match_score,
    create_property_matches_for_profile, create_roommate_matches_for_profile, create_agent_matches_for_profile
)
from property.models import Property


class SearchProfileViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = SearchProfile.objects.select_related('user').prefetch_related('preferred_zones', 'amenities')
    serializer_class = SearchProfileSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Perfiles de búsqueda obtenidos exitosamente',
        'retrieve': 'Perfil de búsqueda obtenido exitosamente',
        'create': 'Perfil de búsqueda creado exitosamente',
        'update': 'Perfil de búsqueda actualizado exitosamente',
        'partial_update': 'Perfil de búsqueda actualizado exitosamente',
        'destroy': 'Perfil de búsqueda eliminado exitosamente',
        'my': 'Perfil de búsqueda del usuario obtenido exitosamente',
        'matches': 'Matches obtenidos exitosamente',
    }

    def get_queryset(self):
        return SearchProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my(self, request):
        profile = SearchProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'error': 'No existe perfil de búsqueda'}, status=status.HTTP_404_NOT_FOUND)
        resp = Response(SearchProfileSerializer(profile).data)
        self.set_response_message(resp, 'Perfil de búsqueda del usuario obtenido exitosamente')
        return resp

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        profile = self.get_object()
        match_type = request.query_params.get('type', 'property')
        status_filter = request.query_params.get('status')  # opcional: pending|accepted|rejected

        # Generar matches on-demand si no existen recientes
        if match_type == 'property':
            create_property_matches_for_profile(profile)
        elif match_type == 'roommate':
            create_roommate_matches_for_profile(profile)
        elif match_type == 'agent':
            create_agent_matches_for_profile(profile)

        qs = Match.objects.filter(target_user=profile.user, match_type=match_type).order_by('-score')
        if status_filter in ['pending', 'accepted', 'rejected']:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MatchSerializer(qs, many=True)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Matches obtenidos exitosamente')
        return resp


class RoommateRequestViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = RoommateRequest.objects.select_related('creator', 'creator__user')
    serializer_class = RoommateRequestSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Solicitudes de roomie obtenidas exitosamente',
        'retrieve': 'Solicitud de roomie obtenida exitosamente',
        'create': 'Solicitud de roomie creada exitosamente',
        'update': 'Solicitud de roomie actualizada exitosamente',
        'partial_update': 'Solicitud de roomie actualizada exitosamente',
        'destroy': 'Solicitud de roomie eliminada exitosamente',
        'my': 'Solicitudes de roomie del usuario obtenidas exitosamente',
    }

    def get_queryset(self):
        return RoommateRequest.objects.filter(creator__user=self.request.user)

    def perform_create(self, serializer):
        profile = SearchProfile.objects.filter(user=self.request.user).first()
        if not profile:
            raise ValueError('Debe crear un SearchProfile antes de crear solicitudes de roomie.')
        serializer.save(creator=profile)

    @action(detail=False, methods=['get'])
    def my(self, request):
        qs = self.get_queryset().order_by('-created_at')
        serializer = RoommateRequestSerializer(qs, many=True)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Solicitudes de roomie del usuario obtenidas exitosamente')
        return resp


class MatchViewSet(MessageConfigMixin, viewsets.GenericViewSet):
    queryset = Match.objects.select_related('target_user')
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'accept': 'Match aceptado exitosamente',
        'reject': 'Match rechazado exitosamente',
        'like': 'Interés registrado exitosamente',
        'pending_requests': 'Solicitudes de match pendientes obtenidas exitosamente',
        'owner_accept': 'Match aceptado por propietario/agente',
        'owner_reject': 'Match rechazado por propietario/agente',
    }

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        match = self.get_object()
        if match.target_user != request.user:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        # Registrar feedback de like
        MatchFeedback.objects.create(
            match=match,
            user=request.user,
            feedback_type='like',
            reason=request.data.get('reason')
        )

        # Notificar al propietario/agente del interés y crear mensaje
        from notification.models import Notification
        if match.match_type == 'property':
            try:
                prop = Property.objects.get(id=match.subject_id)
                from message.models import Message
                Message.objects.create(
                    sender=request.user,
                    receiver=prop.owner,
                    content=f"Hola, me interesa tu propiedad (match {match.score}%)."
                )
                Notification.objects.create(
                    user=prop.owner,
                    message=f"{request.user.username} indicó interés en tu propiedad (match {match.score}%)."
                )

                # Evaluar auto-aceptación si la compatibilidad es muy alta
                from utils.matching import calculate_property_match_score
                profile = SearchProfile.objects.filter(user=request.user).first()
                if profile:
                    new_score, meta = calculate_property_match_score(profile, prop)
                    owner_prefs_score = float(meta.get('details', {}).get('owner_prefs_score', 0))
                    if match.score >= 95 and owner_prefs_score >= 90:
                        match.status = 'accepted'
                        match.save(update_fields=['status', 'updated_at'])
                        Notification.objects.create(
                            user=request.user,
                            message=f"¡Match automático aceptado! Con {prop.owner.username} (score {match.score}%)."
                        )
                        Notification.objects.create(
                            user=prop.owner,
                            message=f"Match automático con {request.user.username} (score {match.score}%)."
                        )
            except Property.DoesNotExist:
                pass

        resp = Response({'status': match.status, 'match': MatchSerializer(match).data})
        self.set_response_message(resp, 'Interés registrado exitosamente')
        return resp

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        match = self.get_object()
        if match.target_user != request.user:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        match.status = 'accepted'
        match.save(update_fields=['status', 'updated_at'])

        # Notificación y mensaje post-match
        from notification.models import Notification
        Notification.objects.create(
            user=request.user,
            message=f"¡Match aceptado! Tipo: {match.match_type}, score {match.score}"
        )

        # Crear conversación básica con propietario/agente si aplica
        if match.match_type == 'property':
            try:
                prop = Property.objects.get(id=match.subject_id)
                from message.models import Message
                Message.objects.create(
                    sender=request.user,
                    receiver=prop.owner,
                    content=f"Hola, me interesa tu propiedad (match {match.score}%)."
                )
                # Notificar al propietario del interés
                Notification.objects.create(
                    user=prop.owner,
                    message=f"{request.user.username} está interesado en tu propiedad (match {match.score}%)."
                )
            except Property.DoesNotExist:
                pass

        resp = Response({'status': 'accepted', 'match': MatchSerializer(match).data})
        self.set_response_message(resp, 'Match aceptado exitosamente')
        return resp

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        match = self.get_object()
        if match.target_user != request.user:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        match.status = 'rejected'
        match.save(update_fields=['status', 'updated_at'])

        reason = request.data.get('reason')
        MatchFeedback.objects.create(
            match=match,
            user=request.user,
            feedback_type='dislike',
            reason=reason
        )

        resp = Response({'status': 'rejected', 'match': MatchSerializer(match).data})
        self.set_response_message(resp, 'Match rechazado exitosamente')
        return resp

    @action(detail=False, methods=['get'], url_path='pending_requests')
    def pending_requests(self, request):
        """
        Lista matches de tipo property con estado pending para propiedades del propietario/agente.
        """
        user = request.user
        # Obtener IDs de propiedades del usuario como owner o agent
        my_props = Property.objects.filter(Q(owner=user) | Q(agent=user)).values_list('id', flat=True)
        qs = Match.objects.filter(match_type='property', status='pending', subject_id__in=list(my_props)).order_by('-score')
        results = []
        for m in qs:
            try:
                prop = Property.objects.get(id=m.subject_id)
            except Property.DoesNotExist:
                continue
            results.append({
                'match': MatchSerializer(m).data,
                'property': {
                    'id': prop.id,
                    'address': prop.address,
                    'price': float(prop.price),
                    'type': prop.type,
                    'bedrooms': prop.bedrooms,
                    'zone_id': getattr(prop.zone, 'id', None),
                    'zone_name': getattr(prop.zone, 'name', None),
                },
                'interested_user': {
                    'id': m.target_user_id,
                    'username': m.target_user.username,
                }
            })
        page = self.paginate_queryset(results)
        if page is not None:
            return self.get_paginated_response(page)
        resp = Response(results)
        self.set_response_message(resp, 'Solicitudes de match pendientes obtenidas exitosamente')
        return resp

    @action(detail=True, methods=['post'], url_path='owner_accept')
    def owner_accept(self, request, pk=None):
        match = self.get_object()
        if match.match_type != 'property':
            return Response({'error': 'Solo disponible para matches de propiedades'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            prop = Property.objects.get(id=match.subject_id)
        except Property.DoesNotExist:
            return Response({'error': 'Propiedad no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        if prop.owner_id != request.user.id and (prop.agent_id != request.user.id if prop.agent_id else True):
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        match.status = 'accepted'
        match.save(update_fields=['status', 'updated_at'])
        
        try:
            from notification.models import Notification
            Notification.objects.create(user=match.target_user, message=f"Tu solicitud de match fue aceptada para la propiedad {prop.address}.")
            Notification.objects.create(user=request.user, message=f"Match aceptado con {match.target_user.username}.")
            
            # Enviar notificación WebSocket en tiempo real
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from message.notification_consumers import send_match_accepted_notification
            
            # Preparar datos del propietario
            owner_data = {
                'id': request.user.id,
                'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'contact': {
                    'email': request.user.email,
                    'phone': getattr(request.user.userprofile, 'phone', '') if hasattr(request.user, 'userprofile') else ''
                }
            }
            
            # Preparar datos de la propiedad
            property_data = {
                'id': prop.id,
                'title': f"{prop.type} en {prop.address}",
                'address': prop.address,
                'price': float(prop.price)
            }
            
            # Preparar datos del match
            match_data = {
                'score': float(match.score),
                'status': match.status
            }
            
            # Enviar notificación asíncrona
            channel_layer = get_channel_layer()
            async_to_sync(send_match_accepted_notification)(
                channel_layer,
                match.target_user.id,
                property_data,
                owner_data,
                match_data
            )
            
        except Exception as e:
            # Log del error pero no interrumpir la respuesta
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar notificación WebSocket de match aceptado: {e}")
            pass
            
        resp = Response({'status': 'accepted', 'match': MatchSerializer(match).data})
        self.set_response_message(resp, 'Match aceptado por propietario/agente')
        return resp

    @action(detail=True, methods=['post'], url_path='owner_reject')
    def owner_reject(self, request, pk=None):
        match = self.get_object()
        if match.match_type != 'property':
            return Response({'error': 'Solo disponible para matches de propiedades'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            prop = Property.objects.get(id=match.subject_id)
        except Property.DoesNotExist:
            return Response({'error': 'Propiedad no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        if prop.owner_id != request.user.id and (prop.agent_id != request.user.id if prop.agent_id else True):
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        match.status = 'rejected'
        match.save(update_fields=['status', 'updated_at'])
        reason = request.data.get('reason')
        try:
            MatchFeedback.objects.create(match=match, user=request.user, feedback_type='dislike', reason=reason)
            from notification.models import Notification
            Notification.objects.create(user=match.target_user, message=f"Tu solicitud de match fue rechazada para la propiedad {prop.address}.")
        except Exception:
            pass
        resp = Response({'status': 'rejected', 'match': MatchSerializer(match).data})
        self.set_response_message(resp, 'Match rechazado por propietario/agente')
        return resp


class MatchFeedbackViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = MatchFeedback.objects.select_related('match', 'user')
    serializer_class = MatchFeedbackSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Feedbacks de match obtenidos exitosamente',
        'retrieve': 'Feedback de match obtenido exitosamente',
        'create': 'Feedback de match creado exitosamente',
        'update': 'Feedback de match actualizado exitosamente',
        'partial_update': 'Feedback de match actualizado exitosamente',
        'destroy': 'Feedback de match eliminado exitosamente',
    }

    def get_queryset(self):
        return MatchFeedback.objects.filter(user=self.request.user)


class RecommendationViewSet(MessageConfigMixin, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Recomendaciones obtenidas exitosamente',
    }

    def list(self, request):
        rec_type = request.query_params.get('type', 'mixed')
        profile = SearchProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'error': 'Debe crear su SearchProfile primero'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        if rec_type in ['mixed', 'property']:
            create_property_matches_for_profile(profile)
            pmatches = Match.objects.filter(target_user=request.user, match_type='property').order_by('-score')[:20]
            results.extend([{'type': 'property', 'match': MatchSerializer(m).data} for m in pmatches])

        if rec_type in ['mixed', 'roommate']:
            create_roommate_matches_for_profile(profile)
            rmatches = Match.objects.filter(target_user=request.user, match_type='roommate').order_by('-score')[:20]
            results.extend([{'type': 'roommate', 'match': MatchSerializer(m).data} for m in rmatches])

        if rec_type in ['mixed', 'agent']:
            create_agent_matches_for_profile(profile)
            amatches = Match.objects.filter(target_user=request.user, match_type='agent').order_by('-score')[:20]
            results.extend([{'type': 'agent', 'match': MatchSerializer(m).data} for m in amatches])

        resp = Response({'results': results})
        self.set_response_message(resp, 'Recomendaciones obtenidas exitosamente')
        return resp