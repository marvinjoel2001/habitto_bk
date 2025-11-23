from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, null=False)
    read_at = models.DateTimeField(blank=True, null=True)
    deleted_for_sender = models.BooleanField(default=False, null=False)
    deleted_for_receiver = models.BooleanField(default=False, null=False)
    edited = models.BooleanField(default=False, null=False)

    def __str__(self):
        return f'Mensaje de {self.sender} a {self.receiver}: {self.content[:50]}'


class WebSocketInteraction(models.Model):
    INTERACTION_TYPES = [
        ('connection', 'Conexión'),
        ('notification_sent', 'Notificación Enviada'),
        ('notification_received', 'Notificación Recibida'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='websocket_interactions')
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES)
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.timestamp}"