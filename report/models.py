from django.db import models
from django.contrib.auth.models import User


class ReportCategory(models.Model):
    CATEGORY_SCOPE_CHOICES = (
        ('profile', 'Perfil'),
        ('property', 'Propiedad'),
        ('both', 'Ambos'),
    )
    name = models.CharField(max_length=100)
    scope = models.CharField(max_length=20, choices=CATEGORY_SCOPE_CHOICES, default='both')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.scope})"


class Report(models.Model):
    TARGET_TYPE_CHOICES = (
        ('user', 'Usuario'),
        ('property', 'Propiedad'),
    )
    STATUS_CHOICES = (
        ('submitted', 'Enviado'),
        ('in_review', 'En revisión'),
        ('resolved', 'Resuelto'),
        ('rejected', 'Rechazado'),
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='reports_received')
    target_property = models.ForeignKey('property.Property', on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    category = models.ForeignKey(ReportCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['target_type', 'status']),
            models.Index(fields=['reporter']),
        ]

    def __str__(self):
        return f"Reporte {self.id} ({self.target_type}) por {self.reporter.username}"


class ReportAttachment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='attachments')
    file_url = models.URLField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjunto {self.id} del reporte {self.report_id}"
