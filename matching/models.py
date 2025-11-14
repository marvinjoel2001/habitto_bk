from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models


class SearchProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='search_profile')
    preferred_zones = models.ManyToManyField('zone.Zone', blank=True)
    location = gis_models.PointField(null=True, blank=True)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    desired_types = models.JSONField(default=list)
    bedrooms_min = models.IntegerField(null=True, blank=True)
    bedrooms_max = models.IntegerField(null=True, blank=True)
    amenities = models.ManyToManyField('amenity.Amenity', blank=True)
    pet_allowed = models.BooleanField(default=False)
    wfh_preference = models.BooleanField(default=False)
    roommate_preference = models.CharField(max_length=20, choices=[('no', 'No'), ('looking', 'Buscando'), ('open', 'Abierto')], default='no')
    roommate_preferences = models.JSONField(default=dict)
    vibes = models.JSONField(default=list)
    semantic_embedding = models.TextField(null=True, blank=True)
    # Nuevos campos para enriquecer matching
    age = models.IntegerField(null=True, blank=True)
    children_count = models.IntegerField(default=0)
    family_size = models.IntegerField(default=1)
    smoker = models.BooleanField(default=False)
    gender = models.CharField(max_length=20, choices=[('male', 'Hombre'), ('female', 'Mujer'), ('other', 'Otro')], null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    has_vehicle = models.BooleanField(default=False)
    commute_distance_km = models.IntegerField(null=True, blank=True)
    education_level = models.CharField(max_length=50, null=True, blank=True)
    pets_count = models.IntegerField(default=0)
    languages = models.JSONField(default=list)
    lifestyle = models.JSONField(default=dict)
    schedule = models.JSONField(default=dict)
    stable_job = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de búsqueda de {self.user.username}"


class RoommateRequest(models.Model):
    creator = models.ForeignKey(SearchProfile, on_delete=models.CASCADE, related_name='roommate_requests')
    desired_move_in_date = models.DateField(null=True, blank=True)
    max_roommates = models.IntegerField(default=2)
    gender_preference = models.CharField(max_length=20, choices=[('male', 'Hombres'), ('female', 'Mujeres'), ('any', 'Cualquiera')], default='any')
    smoker_ok = models.BooleanField(default=False)
    budget_per_person = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Roomie request de {self.creator.user.username}"


class Match(models.Model):
    MATCH_TYPE_CHOICES = (
        ('property', 'Property'),
        ('roommate', 'Roommate'),
        ('agent', 'Agent'),
    )
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES)
    subject_id = models.IntegerField(help_text='ID de Property, RoommateRequest o Agent (User)')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')
    score = models.FloatField()
    metadata = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[('pending', 'Pendiente'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['match_type', 'target_user']),
            models.Index(fields=['match_type', 'subject_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Match {self.match_type} -> {self.target_user.username} ({self.score})"


class MatchFeedback(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_feedback')
    feedback_type = models.CharField(max_length=20, choices=[('like', 'Like'), ('dislike', 'Dislike'), ('neutral', 'Neutral')])
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.feedback_type} por {self.user.username}"