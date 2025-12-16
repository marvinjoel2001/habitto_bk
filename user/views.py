from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserProfile, ProfilePictureHistory
from .models import Block
from .models import UserLocationPoint
from .serializers import UserSerializer, UserCreateSerializer, UserProfileSerializer, ProfilePictureHistorySerializer, UserLocationPointSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def initialize_request(self, request, *args, **kwargs):
        """
        Set action early so get_authenticators can use it.
        """
        method = request.method.lower()
        if method == 'options':
            self.action = 'metadata'
        else:
            self.action = self.action_map.get(method)
        return super().initialize_request(request, *args, **kwargs)

    def get_authenticators(self):
        """
        No requerir autenticación para registro (create)
        """
        if self.action == 'create':
            return []
        return super().get_authenticators()

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

    @action(detail=False, methods=['post'], url_path='submit_verification', permission_classes=[permissions.IsAuthenticated], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def submit_verification(self, request):
        """
        Verificación automática: recibe imágenes de carnet frontal/trasera, selfie y número de documento.
        Marca el perfil como verificado al recibir los datos.
        Campos (multipart/form-data):
        - id_front (file)
        - id_back (file)
        - selfie (file)
        - document_number (string)
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'El usuario no tiene un perfil creado'}, status=status.HTTP_404_NOT_FOUND)

        id_front = request.FILES.get('id_front')
        id_back = request.FILES.get('id_back')
        selfie = request.FILES.get('selfie')
        document_number = request.data.get('document_number')

        updated_fields = []
        if id_front is not None:
            profile.id_card_front = id_front
            updated_fields.append('id_card_front')
        if id_back is not None:
            profile.id_card_back = id_back
            updated_fields.append('id_card_back')
        if selfie is not None:
            profile.selfie = selfie
            updated_fields.append('selfie')
        if document_number:
            profile.document_number = document_number
            updated_fields.append('document_number')

        # Marcar como verificado automáticamente
        profile.is_verified = True
        updated_fields.append('is_verified')
        profile.save(update_fields=updated_fields or ['is_verified'])

        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_user/(?P<user_id>[^/]+)', permission_classes=[permissions.IsAuthenticated])
    def by_user(self, request, user_id=None):
        """
        Obtener el perfil por ID de usuario (evita ambigüedad de query params).
        Respuesta mínima: id de perfil, datos básicos del usuario y foto.
        """
        try:
            user_obj = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Verificar bloqueo en ambos sentidos
        if Block.objects.filter(blocker=request.user, blocked=user_obj).exists() or Block.objects.filter(blocker=user_obj, blocked=request.user).exists():
            return Response({'detail': 'Acceso bloqueado'}, status=status.HTTP_403_FORBIDDEN)
        try:
            profile = UserProfile.objects.get(user=user_obj)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        full_name = ((user_obj.first_name or '').strip() + ' ' + (user_obj.last_name or '').strip()).strip() or user_obj.username
        picture_url = None
        if profile.profile_picture:
            try:
                picture_url = request.build_absolute_uri(profile.profile_picture.url)
            except Exception:
                picture_url = profile.profile_picture.url

        data = {
            'profile_id': profile.id,
            'user': {
                'id': user_obj.id,
                'username': user_obj.username,
                'full_name': full_name,
                'email': user_obj.email,
            },
            'profile_picture': picture_url,
            'user_type': profile.user_type,
            'is_verified': profile.is_verified,
        }
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def block(self, request):
        other_id = request.data.get('other_user_id') or request.query_params.get('other_user_id')
        if not other_id:
            return Response({'detail': 'other_user_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other = User.objects.get(id=int(other_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if other.id == request.user.id:
            return Response({'detail': 'No puede bloquearse a sí mismo'}, status=status.HTTP_400_BAD_REQUEST)
        Block.objects.get_or_create(blocker=request.user, blocked=other)
        try:
            from notification.models import Notification
            Notification.objects.create(user=request.user, message=f'Has bloqueado a {other.username}.')
        except Exception:
            pass
        return Response({'status': 'blocked', 'other_user_id': other.id})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unblock(self, request):
        other_id = request.data.get('other_user_id') or request.query_params.get('other_user_id')
        if not other_id:
            return Response({'detail': 'other_user_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other = User.objects.get(id=int(other_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        Block.objects.filter(blocker=request.user, blocked=other).delete()
        try:
            from notification.models import Notification
            Notification.objects.create(user=request.user, message=f'Has desbloqueado a {other.username}.')
        except Exception:
            pass
        return Response({'status': 'unblocked', 'other_user_id': other.id})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def blocked(self, request):
        qs = Block.objects.filter(blocker=request.user).select_related('blocked').order_by('-created_at')
        results = [{'id': b.blocked.id, 'username': b.blocked.username, 'first_name': b.blocked.first_name, 'last_name': b.blocked.last_name} for b in qs]
        return Response({'count': len(results), 'results': results})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def request_delete_account(self, request):
        """
        Solicita eliminación de cuenta: se marca como pendiente y se agenda para 30 días.
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        now = timezone.now()
        profile.deletion_pending = True
        profile.deletion_requested_at = now
        profile.deletion_scheduled_for = now + timedelta(days=30)
        profile.save(update_fields=['deletion_pending', 'deletion_requested_at', 'deletion_scheduled_for'])
        try:
            from notification.models import Notification
            Notification.objects.create(user=request.user, message='Tu cuenta será eliminada en 30 días. Si vuelves a iniciar sesión, se cancelará la eliminación.')
        except Exception:
            pass
        return Response({
            'status': 'deletion_scheduled',
            'scheduled_for': profile.deletion_scheduled_for
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel_delete_account(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        profile.deletion_pending = False
        profile.deletion_requested_at = None
        profile.deletion_scheduled_for = None
        profile.save(update_fields=['deletion_pending', 'deletion_requested_at', 'deletion_scheduled_for'])
        try:
            from notification.models import Notification
            Notification.objects.create(user=request.user, message='La eliminación de tu cuenta ha sido cancelada.')
        except Exception:
            pass
        return Response({'status': 'deletion_cancelled'})


class UserTokenObtainPairView(TokenObtainPairView):
    """
    Login JWT que además cancela eliminación pendiente si el usuario inicia sesión.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = (request.data or {}).get('username')
            try:
                user_obj = User.objects.filter(username=username).first()
                if user_obj:
                    profile = UserProfile.objects.filter(user=user_obj).first()
                    if profile and profile.deletion_pending:
                        profile.deletion_pending = False
                        profile.deletion_requested_at = None
                        profile.deletion_scheduled_for = None
                        profile.save(update_fields=['deletion_pending', 'deletion_requested_at', 'deletion_scheduled_for'])
            except Exception:
                pass
        return response


class UserLocationPointViewSet(viewsets.ModelViewSet):
    queryset = UserLocationPoint.objects.select_related('user').order_by('-created_at')
    serializer_class = UserLocationPointSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        start = self.request.query_params.get('from')
        end = self.request.query_params.get('to')
        try:
            if start:
                start_dt = timezone.datetime.fromisoformat(start)
                qs = qs.filter(created_at__gte=start_dt)
            if end:
                end_dt = timezone.datetime.fromisoformat(end)
                qs = qs.filter(created_at__lte=end_dt)
        except Exception:
            pass
        return qs

    @action(detail=False, methods=['post'])
    def submit(self, request):
        from django.contrib.gis.geos import Point
        try:
            lat = float(request.data.get('latitude'))
            lng = float(request.data.get('longitude'))
        except (TypeError, ValueError):
            return Response({'detail': 'latitude y longitude son requeridos y deben ser numéricos'}, status=status.HTTP_400_BAD_REQUEST)
        point = Point(lng, lat, srid=4326)
        obj = UserLocationPoint.objects.create(user=request.user, location=point)
        ser = self.get_serializer(obj)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def route(self, request):
        from datetime import timedelta
        period = (request.query_params.get('period') or 'day').lower()
        date_str = request.query_params.get('date')
        now = timezone.now()
        if date_str:
            try:
                base_date = timezone.datetime.fromisoformat(date_str)
            except Exception:
                base_date = now
        else:
            base_date = now

        start = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == 'day':
            end = start + timedelta(days=1)
        elif period == 'week':
            start = start - timedelta(days=start.weekday())
            end = start + timedelta(days=7)
        elif period == 'month':
            start = start.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        elif period == 'year':
            start = start.replace(month=1, day=1)
            end = start.replace(year=start.year + 1)
        else:
            return Response({'detail': 'period inválido. Use day|week|month|year'}, status=status.HTTP_400_BAD_REQUEST)

        points = UserLocationPoint.objects.filter(user=request.user, created_at__gte=start, created_at__lt=end).order_by('created_at')
        coords = [[p.location.x, p.location.y] for p in points]
        ser = self.get_serializer(points, many=True)
        geojson = {
            'type': 'LineString',
            'coordinates': coords
        }
        return Response({'period': period, 'from': start, 'to': end, 'count': len(coords), 'points': ser.data, 'geojson': geojson})

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
