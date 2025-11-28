from rest_framework import serializers
from .models import Report, ReportCategory, ReportAttachment


class ReportAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportAttachment
        fields = ['id', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategory
        fields = ['id', 'name', 'scope', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    attachments = ReportAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'target_type', 'target_user', 'target_property',
            'category', 'title', 'description', 'severity', 'status', 'admin_notes',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reporter', 'status', 'admin_notes', 'created_at', 'updated_at']

    def validate(self, data):
        target_type = data.get('target_type')
        target_user = data.get('target_user')
        target_property = data.get('target_property')
        if target_type == 'user' and not target_user:
            raise serializers.ValidationError('Debe especificar target_user para reportes de usuario.')
        if target_type == 'property' and not target_property:
            raise serializers.ValidationError('Debe especificar target_property para reportes de propiedad.')
        if data.get('title') is None or not str(data.get('title')).strip():
            raise serializers.ValidationError('El título es obligatorio.')
        if data.get('description') is None or len(str(data.get('description')).strip()) < 10:
            raise serializers.ValidationError('La descripción debe tener al menos 10 caracteres.')
        return data
