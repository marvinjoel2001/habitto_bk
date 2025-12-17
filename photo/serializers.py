from rest_framework import serializers
from .models import Photo

class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Photo
        fields = ['id', 'property', 'image', 'image_url', 'caption', 'created_at']
        read_only_fields = ['id', 'created_at', 'image_url']