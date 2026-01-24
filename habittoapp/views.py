from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from bk_habitto.mixins import MessageConfigMixin
from .serializers import ContactMessageSerializer
from .tasks import send_contact_email_task


class ContactMessageView(MessageConfigMixin, APIView):
    permission_classes = [AllowAny]
    success_messages = {'post': 'Mensaje enviado exitosamente'}

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        to_email = getattr(settings, 'CONTACT_RECIPIENT_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        
        if not to_email:
            return Response({'detail': 'Email no configurado.'}, status=500)

        # Enviar correo de forma asíncrona para evitar timeouts
        send_contact_email_task.delay(data)

        return Response({'status': 'sent', 'to': to_email})
