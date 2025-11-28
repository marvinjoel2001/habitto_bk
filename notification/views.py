from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from bk_habitto.mixins import MessageConfigMixin

class NotificationViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Notificaciones obtenidas exitosamente',
        'retrieve': 'Notificación obtenida exitosamente',
        'create': 'Notificación creada exitosamente',
        'update': 'Notificación actualizada exitosamente',
        'partial_update': 'Notificación actualizada exitosamente',
        'destroy': 'Notificación eliminada exitosamente',
        'mark_as_read': 'Notificación marcada como leída exitosamente',
        'my': 'Notificaciones del usuario obtenidas exitosamente',
    }
    
    def get_queryset(self):
        qs = super().get_queryset()
        if not getattr(self.request, 'user', None) or not self.request.user.is_authenticated:
            return qs.none()
        qs = qs.filter(user=self.request.user)
        is_read = self.request.query_params.get('is_read')
        if str(is_read).lower() in ['true', '1']:
            qs = qs.filter(is_read=True)
        elif str(is_read).lower() in ['false', '0']:
            qs = qs.filter(is_read=False)
        return qs
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Notificación marcada como leída exitosamente')
        return resp

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        user = request.user
        notifications = self.get_queryset().order_by('-created_at')
        notifications_data = self.get_serializer(notifications, many=True).data
        from message.models import Message
        msgs_qs = Message.objects.filter(receiver=user, deleted_for_receiver=False).order_by('-created_at')
        unread_count = msgs_qs.filter(is_read=False).count()
        latest_msgs = msgs_qs[:50]
        from message.serializers import MessageSerializer
        messages_data = MessageSerializer(latest_msgs, many=True).data
        try:
            from matching.models import MatchFeedback
            from property.models import Property as PropertyModel
            property_ids = list(PropertyModel.objects.filter(owner=user).values_list('id', flat=True))
            feedback_qs = MatchFeedback.objects.select_related('match', 'user').filter(
                match__match_type='property',
                match__subject_id__in=property_ids,
                feedback_type='like'
            ).order_by('-created_at')
            props = {p.id: p for p in PropertyModel.objects.filter(id__in=property_ids)}
            likes_results = []
            for fb in feedback_qs[:200]:
                prop = props.get(fb.match.subject_id)
                likes_results.append({
                    'property_id': fb.match.subject_id,
                    'property_title': f"{getattr(prop, 'type', '')} en {getattr(prop, 'address', '')}" if prop else None,
                    'liker': {
                        'id': fb.user.id,
                        'username': fb.user.username,
                        'first_name': fb.user.first_name,
                        'last_name': fb.user.last_name,
                        'email': fb.user.email,
                    },
                    'score': fb.match.score,
                    'created_at': fb.created_at,
                })
        except Exception:
            likes_results = []
        payload = {
            'notifications': notifications_data,
            'messages': {
                'count': msgs_qs.count(),
                'unread_count': unread_count,
                'latest': messages_data,
            },
            'likes': {
                'count': len(likes_results),
                'results': likes_results,
            }
        }
        resp = Response(payload)
        self.set_response_message(resp, 'Notificaciones del usuario obtenidas exitosamente')
        return resp
