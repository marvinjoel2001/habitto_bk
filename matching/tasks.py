from celery import shared_task
from .models import SearchProfile
from utils.matching import (
    create_property_matches_for_profile, create_roommate_matches_for_profile, create_agent_matches_for_profile
)


@shared_task
def compute_matches_for_profile(profile_id: int):
    profile = SearchProfile.objects.get(id=profile_id)
    create_property_matches_for_profile(profile)
    create_roommate_matches_for_profile(profile)
    create_agent_matches_for_profile(profile)