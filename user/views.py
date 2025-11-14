from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import User
from .models import UserProfile, ProfilePictureHistory
from .serializers import UserSerializer, UserCreateSerializer, UserProfileSerializer, ProfilePictureHistorySerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Permitir registro público pero requerir autenticación para otras acciones
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Obtener información del usuario actual autenticado
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by('-created_at')
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        """
        Asignar automáticamente el usuario autenticado al perfil
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Obtener perfil del usuario actual autenticado
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'El usuario no tiene un perfil creado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_me(self, request):
        """
        Actualizar perfil del usuario actual autenticado
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'El usuario no tiene un perfil creado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_profile_picture(self, request):
        """
        Subir o actualizar foto de perfil del usuario actual
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            if 'profile_picture' not in request.FILES:
                return Response(
                    {'detail': 'No se proporcionó ninguna imagen'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Marcar todas las fotos anteriores como no actuales
            ProfilePictureHistory.objects.filter(
                user_profile=profile,
                is_current=True
            ).update(is_current=False)

            # Actualizar la foto de perfil
            new_picture = request.FILES['profile_picture']
            profile.profile_picture = new_picture
            profile.save()

            # Crear nueva entrada en el historial
            ProfilePictureHistory.objects.create(
                user_profile=profile,
                image=new_picture,
                original_filename=new_picture.name,
                is_current=True
            )

            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'El usuario no tiene un perfil creado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def picture_history(self, request):
        """
        Obtener historial de fotos de perfil del usuario actual
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            history = ProfilePictureHistory.objects.filter(
                user_profile=profile
            ).order_by('-uploaded_at')
            serializer = ProfilePictureHistorySerializer(history, many=True)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'El usuario no tiene un perfil creado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        profile = self.get_object()
        profile.is_verified = True
        profile.save()
        return Response({'status': 'verified'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_favorite(self, request):
        """
        Agrega una propiedad a favoritos del usuario actual.
        Body: { "property_id": <int> }
        """
        prop_id = request.data.get('property_id')
        if not prop_id:
            return Response({'detail': 'property_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from property.models import Property
            prop = Property.objects.get(id=prop_id)
        except Property.DoesNotExist:
            return Response({'detail': 'Propiedad no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        profile = UserProfile.objects.get(user=request.user)
        profile.favorites.add(prop)
        return Response({'status': 'added', 'property_id': prop_id})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_favorite(self, request):
        """
        Elimina una propiedad de favoritos del usuario actual.
        Body: { "property_id": <int> }
        """
        prop_id = request.data.get('property_id')
        if not prop_id:
            return Response({'detail': 'property_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from property.models import Property
            prop = Property.objects.get(id=prop_id)
        except Property.DoesNotExist:
            return Response({'detail': 'Propiedad no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        profile = UserProfile.objects.get(user=request.user)
        profile.favorites.remove(prop)
        return Response({'status': 'removed', 'property_id': prop_id})
