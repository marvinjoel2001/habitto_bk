from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
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
        msgs = Message.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender', 'receiver').order_by('-created_at')
        conv_map = {}
        results = []
        for m in msgs:
            other = m.receiver if m.sender_id == user.id else m.sender
            if other.id not in conv_map:
                conv_map[other.id] = True
                results.append({
                    'counterpart': {'id': other.id, 'username': other.username},
                    'last_message': {
                        'id': m.id,
                        'content': m.content,
                        'created_at': m.created_at,
                        'sender': m.sender_id,
                        'receiver': m.receiver_id,
                    }
                })
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
