from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Report, ReportCategory, ReportAttachment
from .serializers import ReportSerializer, ReportCategorySerializer, ReportAttachmentSerializer
from bk_habitto.mixins import MessageConfigMixin


class ReportCategoryViewSet(MessageConfigMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ReportCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = ReportCategorySerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Categorías de reporte obtenidas exitosamente',
        'retrieve': 'Categoría de reporte obtenida exitosamente',
    }


class ReportViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Report.objects.select_related('reporter', 'target_user', 'target_property', 'category').order_by('-created_at')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    success_messages = {
        'list': 'Reportes obtenidos exitosamente',
        'retrieve': 'Reporte obtenido exitosamente',
        'create': 'Reporte enviado exitosamente',
        'update': 'Reporte actualizado exitosamente',
        'partial_update': 'Reporte actualizado exitosamente',
        'destroy': 'Reporte eliminado exitosamente',
        'my': 'Mis reportes obtenidos exitosamente',
        'add_attachment': 'Adjunto agregado exitosamente',
        'update_status': 'Estado del reporte actualizado exitosamente',
    }

    def get_queryset(self):
        # Admin ve todos; usuarios ven solo los que crearon
        if getattr(self.request.user, 'is_staff', False):
            return self.queryset
        return self.queryset.filter(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        # Protección básica contra abuso: máximo 10 reportes por hora
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_count = Report.objects.filter(reporter=request.user, created_at__gte=one_hour_ago).count()
        if recent_count >= 10:
            return Response({'detail': 'Límite de reportes por hora alcanzado'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        data = request.data.copy()
        data['reporter'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(reporter=request.user)

        # Notificar al usuario que se recibió el reporte
        try:
            from notification.models import Notification
            Notification.objects.create(user=request.user, message=f"Tu reporte #{report.id} fue recibido y está en estado 'submitted'.")
        except Exception:
            pass

        resp = Response(self.get_serializer(report).data, status=status.HTTP_201_CREATED)
        self.set_response_message(resp, 'Reporte enviado exitosamente')
        return resp

    @action(detail=False, methods=['get'])
    def my(self, request):
        qs = Report.objects.filter(reporter=request.user).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Mis reportes obtenidos exitosamente')
        return resp

    @action(detail=True, methods=['post'], url_path='add_attachment')
    def add_attachment(self, request, pk=None):
        report = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Archivo requerido'}, status=status.HTTP_400_BAD_REQUEST)
        att = ReportAttachment.objects.create(report=report, file=file)
        serializer = ReportAttachmentSerializer(att)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Adjunto agregado exitosamente')
        return resp

    @action(detail=True, methods=['post'], url_path='update_status')
    def update_status(self, request, pk=None):
        # Solo staff puede cambiar estado
        if not getattr(request.user, 'is_staff', False):
            return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        report = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Report.STATUS_CHOICES).keys():
            return Response({'detail': 'Estado inválido'}, status=status.HTTP_400_BAD_REQUEST)
        report.status = new_status
        report.admin_notes = request.data.get('admin_notes') or report.admin_notes
        report.save(update_fields=['status', 'admin_notes', 'updated_at'])

        # Notificar al usuario sobre el cambio de estado
        try:
            from notification.models import Notification
            Notification.objects.create(user=report.reporter, message=f"Tu reporte #{report.id} cambió a estado '{new_status}'.")
        except Exception:
            pass

        resp = Response(self.get_serializer(report).data)
        self.set_response_message(resp, 'Estado del reporte actualizado exitosamente')
        return resp
