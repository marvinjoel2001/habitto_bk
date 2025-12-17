from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, ProfilePictureHistory, UserLocationPoint
from bk_habitto.services.cloudinary_service import CloudinaryService

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class ProfilePictureHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePictureHistory
        fields = ['id', 'image_url', 'original_filename', 'uploaded_at', 'is_current']
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
    profile_picture_url = serializers.URLField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'user_type', 'phone', 'profile_picture', 'profile_picture_url']

    def create(self, validated_data):
        # Extraer datos del perfil
        user_type = validated_data.pop('user_type', 'inquilino')
        phone = validated_data.pop('phone', '')
        profile_picture = validated_data.pop('profile_picture', None)
        profile_picture_url = validated_data.pop('profile_picture_url', None)

        # Si se subió un archivo, subirlo a Cloudinary
        if profile_picture:
            try:
                uploaded_url = CloudinaryService.upload_image(profile_picture, folder="habitto/profiles")
                if uploaded_url:
                    profile_picture_url = uploaded_url
            except Exception:
                pass

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
            profile_picture_url=profile_picture_url
        )

        # Si hay URL de foto, crear entrada en el historial
        if profile_picture_url:
            ProfilePictureHistory.objects.create(
                user_profile=profile,
                image_url=profile_picture_url,
                original_filename=profile_picture.name if profile_picture else 'url_upload',
                is_current=True
            )

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    picture_history = ProfilePictureHistorySerializer(many=True, read_only=True)
    profile_picture = serializers.ImageField(write_only=True, required=False)
    id_card_front = serializers.ImageField(write_only=True, required=False)
    id_card_back = serializers.ImageField(write_only=True, required=False)
    selfie = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_id', 'user_type', 'phone',
            'profile_picture', 'profile_picture_url',
            'is_verified',
            'id_card_front', 'id_card_front_url',
            'id_card_back', 'id_card_back_url',
            'selfie', 'selfie_url',
            'document_number',
            'created_at', 'updated_at', 'favorites', 'picture_history'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Manejar historial si cambia la foto
        new_picture = validated_data.pop('profile_picture', None)
        new_picture_url = validated_data.get('profile_picture_url')

        # Manejar otras imágenes (verificación) - subida a Cloudinary
        for field in ['id_card_front', 'id_card_back', 'selfie']:
            img = validated_data.pop(field, None)
            if img:
                try:
                    url = CloudinaryService.upload_image(img, folder=f"habitto/verification/{field}")
                    validated_data[f'{field}_url'] = url
                except Exception:
                    pass

        # Si hay nueva foto de perfil (archivo), subirla
        if new_picture:
            try:
                uploaded_url = CloudinaryService.upload_image(new_picture, folder="habitto/profiles")
                if uploaded_url:
                    new_picture_url = uploaded_url
                    validated_data['profile_picture_url'] = new_picture_url
            except Exception:
                pass

        if new_picture_url and new_picture_url != instance.profile_picture_url:
            # Marcar anteriores como no actuales
            ProfilePictureHistory.objects.filter(
                user_profile=instance,
                is_current=True
            ).update(is_current=False)

            # Crear nueva entrada
            ProfilePictureHistory.objects.create(
                user_profile=instance,
                image_url=new_picture_url,
                original_filename=new_picture.name if new_picture else 'url_update',
                is_current=True
            )

        return super().update(instance, validated_data)

class UserLocationPointSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = UserLocationPoint
        fields = ['id', 'user', 'location', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        return obj.location.x if obj.location else None

    def create(self, validated_data):
        # Remover user_id si está presente, ya que se maneja en la vista
        validated_data.pop('user_id', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Si se está actualizando la foto de perfil, manejar el historial
        # Nota: Este método parece estar en el serializer incorrecto (UserLocationPoint no tiene profile_picture)
        # pero mantenemos la lógica corregida por si acaso se usa para actualizar perfil indirectamente
        # aunque probablemente sea código muerto o copiado.
        if 'profile_picture' in validated_data and validated_data['profile_picture']:
            new_picture = validated_data.pop('profile_picture')
            try:
                url = CloudinaryService.upload_image(new_picture, folder="habitto/profiles")

                # Acceder al perfil del usuario
                profile = instance.user.profile
                profile.profile_picture_url = url
                profile.save()

                # Marcar todas las fotos anteriores como no actuales
                ProfilePictureHistory.objects.filter(
                    user_profile=profile,
                    is_current=True
                ).update(is_current=False)

                # Crear nueva entrada en el historial
                ProfilePictureHistory.objects.create(
                    user_profile=profile,
                    image_url=url,
                    original_filename=new_picture.name,
                    is_current=True
                )
            except Exception:
                pass

        return super().update(instance, validated_data)
