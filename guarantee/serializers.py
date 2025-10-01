from rest_framework import serializers
from .models import Guarantee

class GuaranteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guarantee
        fields = '__all__'
        read_only_fields = ['id', 'created_at']