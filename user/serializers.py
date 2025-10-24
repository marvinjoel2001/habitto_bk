from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, ProfilePictureHistory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class ProfilePictureHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePictureHistory
        fields = ['id', 'image', 'original_filename', 'uploaded_at', 'is_current']
        read_only_fields = ['id', 'uploaded_at']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        write_only=True,
        required=False,
        default='inquilino'
    )
    phone = serializers.CharField(write_only=True, required=False, default='')
    profile_picture = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'user_type', 'phone', 'profile_picture']

    def create(self, validated_data):
        # Extraer datos del perfil
        user_type = validated_data.pop('user_type', 'inquilino')
        phone = validated_data.pop('phone', '')
        profile_picture = validated_data.pop('profile_picture', None)

        # Crear usuario
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Crear perfil automáticamente
        profile = UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            profile_picture=profile_picture
        )

        # Si se subió una foto, crear entrada en el historial
        if profile_picture:
            ProfilePictureHistory.objects.create(
                user_profile=profile,
                image=profile_picture,
                original_filename=profile_picture.name,
                is_current=True
            )

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    picture_history = ProfilePictureHistorySerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'user_id', 'user_type', 'phone', 'profile_picture', 'is_verified', 'created_at', 'updated_at', 'favorites', 'picture_history']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Remover user_id si está presente, ya que se maneja en la vista
        validated_data.pop('user_id', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Si se está actualizando la foto de perfil, manejar el historial
        if 'profile_picture' in validated_data and validated_data['profile_picture']:
            new_picture = validated_data['profile_picture']

            # Marcar todas las fotos anteriores como no actuales
            ProfilePictureHistory.objects.filter(
                user_profile=instance,
                is_current=True
            ).update(is_current=False)

            # Crear nueva entrada en el historial
            ProfilePictureHistory.objects.create(
                user_profile=instance,
                image=new_picture,
                original_filename=new_picture.name,
                is_current=True
            )

        return super().update(instance, validated_data)
