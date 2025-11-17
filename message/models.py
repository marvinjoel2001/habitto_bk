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