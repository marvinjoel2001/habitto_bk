from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from bk_habitto.mixins import MessageConfigMixin
from .serializers import ContactMessageSerializer


class ContactMessageView(MessageConfigMixin, APIView):
    permission_classes = [AllowAny]
    success_messages = {'post': 'Mensaje enviado exitosamente'}

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        to_email = getattr(settings, 'CONTACT_RECIPIENT_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or to_email

        if not to_email or not from_email:
            return Response({'detail': 'Email no configurado.'}, status=500)

        subject = f"[Contacto] {data['subject']}"
        context = {
            'full_name': data['full_name'],
            'email': data['email'],
            'subject': data['subject'],
            'message': data['message'],
            'sent_at': timezone.now(),
            'logo_url': data.get('logo_url'),
            'content_image_url': data.get('content_image_url'),
        }
        html_body = render_to_string('contact_email.html', context)
        text_body = (
            f"Nuevo mensaje de {data['full_name']} <{data['email']}>\n"
            f"Asunto: {data['subject']}\n\n"
            f"{data['message']}\n"
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[to_email],
            reply_to=[data['email']]
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)

        return Response({'status': 'sent', 'to': to_email})
