from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from bk_habitto.mixins import MessageConfigMixin
from .models import Message
from .serializers import MessageSerializer

class MessageViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    class MessagePagination(PageNumberPagination):
        page_size = 50
        page_size_query_param = 'page_size'
        max_page_size = 100
    pagination_class = MessagePagination
    success_messages = {
        'list': 'Mensajes obtenidos exitosamente',
        'retrieve': 'Mensaje obtenido exitosamente',
        'create': 'Mensaje creado exitosamente',
        'update': 'Mensaje actualizado exitosamente',
        'partial_update': 'Mensaje actualizado exitosamente',
        'destroy': 'Mensaje eliminado exitosamente',
    }

    @action(detail=False, methods=['get'], url_path='conversations')
    def conversations(self, request):
        user = request.user
        counterpart_filter = request.query_params.get('counterpart')
        include_messages_param = request.query_params.get('include_messages')
        include_messages = str(include_messages_param).lower() in ['1', 'true', 'yes']
        messages_page = int(request.query_params.get('messages_page') or 1)
        messages_page_size = int(request.query_params.get('messages_page_size') or 50)
        msgs = Message.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender', 'receiver').order_by('-created_at')
        conv_map = {}
        results = []
        for m in msgs:
            other = m.receiver if m.sender_id == user.id else m.sender
            if counterpart_filter and str(other.id) != str(counterpart_filter):
                continue
            if other.id not in conv_map:
                conv_map[other.id] = True
                profile = None
                try:
                    from user.models import UserProfile
                    profile = UserProfile.objects.select_related('user').filter(user_id=other.id).first()
                except Exception:
                    profile = None
                full_name = ((other.first_name or '').strip() + ' ' + (other.last_name or '').strip()).strip() or other.username
                picture_url = None
                if profile and profile.profile_picture:
                    try:
                        picture_url = request.build_absolute_uri(profile.profile_picture.url)
                    except Exception:
                        picture_url = profile.profile_picture.url
                last_msg = {
                    'id': m.id,
                    'content': m.content,
                    'created_at': m.created_at,
                    'createdAt': m.created_at,
                    'sender': m.sender_id,
                    'receiver': m.receiver_id,
                    'is_read': getattr(m, 'is_read', False),
                    'read_at': getattr(m, 'read_at', None),
                    'room_id': f"{min(user.id, other.id)}-{max(user.id, other.id)}",
                    'roomId': f"{min(user.id, other.id)}-{max(user.id, other.id)}",
                }
                payload = {
                    'counterpart': {
                        'id': other.id,
                        'username': other.username,
                        'full_name': full_name,
                        'profile_picture': picture_url,
                    },
                    'last_message': last_msg,
                    'unread_count': Message.objects.filter(sender_id=other.id, receiver_id=user.id, is_read=False).count()
                }
                if include_messages:
                    thread_qs = Message.objects.filter(
                        (Q(sender_id=user.id) & Q(receiver_id=other.id)) |
                        (Q(sender_id=other.id) & Q(receiver_id=user.id))
                    ).order_by('created_at')
                    total = thread_qs.count()
                    start = max((messages_page - 1) * messages_page_size, 0)
                    end = start + messages_page_size
                    page_qs = thread_qs[start:end]
                    thread = MessageSerializer(page_qs, many=True).data
                    payload['messages'] = thread
                    payload['last_message'] = thread[-1] if thread else payload['last_message']
                    payload['messages_pagination'] = {
                        'page': messages_page,
                        'page_size': messages_page_size,
                        'total': total,
                        'has_next': end < total,
                        'has_previous': start > 0,
                    }
                results.append(payload)
        page = self.paginate_queryset(results)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(results)

    @action(detail=False, methods=['get'], url_path='thread')
    def thread(self, request):
        user = request.user
        other_id = request.query_params.get('other_user_id')
        if not other_id:
            return Response({'detail': 'other_user_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other_id = int(other_id)
        except ValueError:
            return Response({'detail': 'other_user_id inválido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = Message.objects.filter(
            (Q(sender_id=user.id) & Q(receiver_id=other_id)) |
            (Q(sender_id=other_id) & Q(receiver_id=user.id))
        ).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        try:
            msg = Message.objects.get(id=int(pk))
        except (Message.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Mensaje no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if msg.receiver_id != request.user.id:
            return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        if not msg.is_read:
            msg.is_read = True
            msg.read_at = timezone.now()
            msg.save(update_fields=['is_read', 'read_at'])
        return Response({'status': 'ok', 'message_id': msg.id, 'is_read': msg.is_read})

    @action(detail=False, methods=['post'], url_path='mark_thread_read')
    def mark_thread_read(self, request):
        other_id = request.data.get('other_user_id') or request.query_params.get('other_user_id')
        if not other_id:
            return Response({'detail': 'other_user_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other_id = int(other_id)
        except ValueError:
            return Response({'detail': 'other_user_id inválido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = Message.objects.filter(sender_id=other_id, receiver_id=request.user.id, is_read=False)
        updated = qs.update(is_read=True, read_at=timezone.now())
        return Response({'status': 'ok', 'updated': updated})
