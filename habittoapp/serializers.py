from rest_framework import serializers


class ContactMessageSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    logo_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    content_image_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
