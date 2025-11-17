from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import SearchProfile, RoommateRequest, Match, MatchFeedback
from amenity.models import Amenity


class AmenityFlexibleField(serializers.Field):
    def to_internal_value(self, data):
        if data is None:
            return []
        if not isinstance(data, list):
            raise serializers.ValidationError('amenities debe ser una lista')
        result = []
        for item in data:
            try:
                if isinstance(item, int):
                    a = Amenity.objects.get(id=item)
                    result.append(a)
                    continue
                if isinstance(item, str):
                    raw = item.strip()
                    if raw.isdigit():
                        a = Amenity.objects.get(id=int(raw))
                        result.append(a)
                    else:
                        existing = Amenity.objects.filter(name__iexact=raw).first()
                        if existing:
                            result.append(existing)
                        else:
                            result.append(Amenity.objects.create(name=raw))
                    continue
            except Amenity.DoesNotExist:
                raise serializers.ValidationError('Amenity no encontrada')
        return result

    def to_representation(self, value):
        return [a.id for a in value.all()]

class SearchProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, write_only=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, write_only=True)
    amenities = AmenityFlexibleField(required=False)
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
        amenities_data = validated_data.pop('amenities', None)
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        if lat is not None and lng is not None:
            validated_data['location'] = Point(float(lng), float(lat))
        instance = super().create(validated_data)
        if amenities_data is not None:
            instance.amenities.set(amenities_data)
        return instance

    def update(self, instance, validated_data):
        amenities_data = validated_data.pop('amenities', None)
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        if lat is not None and lng is not None:
            instance.location = Point(float(lng), float(lat))
        instance = super().update(instance, validated_data)
        if amenities_data is not None:
            instance.amenities.set(amenities_data)
        return instance


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