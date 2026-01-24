from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_contact_email_task(data):
    """
    Task to send contact email asynchronously.
    """
    try:
        to_email = getattr(settings, 'CONTACT_RECIPIENT_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or to_email

        if not to_email or not from_email:
            logger.error("Email configuration missing for send_contact_email_task")
            return "Email configuration missing"

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

        logger.info(f"Contact email sent to {to_email}")
        return f"Sent to {to_email}"

    except Exception as e:
        logger.error(f"Failed to send contact email: {e}")
        raise e
