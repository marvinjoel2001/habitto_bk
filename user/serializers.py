from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        write_only=True,
        required=False,
        default='inquilino'
    )
    phone = serializers.CharField(write_only=True, required=False, default='')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'user_type', 'phone']
    
    def create(self, validated_data):
        # Extraer datos del perfil
        user_type = validated_data.pop('user_type', 'inquilino')
        phone = validated_data.pop('phone', '')
        
        # Crear usuario
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Crear perfil automáticamente
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone
        )
        
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'user_id', 'user_type', 'phone', 'is_verified', 'created_at', 'updated_at', 'favorites']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Remover user_id si está presente, ya que se maneja en la vista
        validated_data.pop('user_id', None)
        return super().create(validated_data)