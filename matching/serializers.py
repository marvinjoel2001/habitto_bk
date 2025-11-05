from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import SearchProfile, RoommateRequest, Match, MatchFeedback


class SearchProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, write_only=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, write_only=True)
    # Campos adicionales se serializan automáticamente vía fields='__all__'

    class Meta:
        model = SearchProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'location']

    def validate(self, data):
        lat = data.get('latitude')
        lng = data.get('longitude')
        if (lat is not None and lng is None) or (lng is not None and lat is None):
            raise serializers.ValidationError('Debe proporcionar latitude y longitude juntas.')
        return data

    def create(self, validated_data):
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        if lat is not None and lng is not None:
            validated_data['location'] = Point(float(lng), float(lat))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        if lat is not None and lng is not None:
            instance.location = Point(float(lng), float(lat))
        return super().update(instance, validated_data)


class RoommateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoommateRequest
        fields = '__all__'
        read_only_fields = ['creator', 'created_at', 'updated_at']


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'
        read_only_fields = ['status', 'created_at', 'updated_at']


class MatchFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchFeedback
        fields = '__all__'
        read_only_fields = ['created_at']