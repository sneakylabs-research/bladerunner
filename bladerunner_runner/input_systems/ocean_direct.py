"""
OCEAN Direct input system.

Programs personality using explicit numeric scores.
"Openness: 75/100, Conscientiousness: 25/100..."

This is the baseline approach. Clear, unambiguous, easily reproducible.
"""

from .base import BaseInputSystem
from ..models import OceanProfile


class OceanDirectSystem(BaseInputSystem):
    """Direct numeric OCEAN score programming."""
    
    def get_name(self) -> str:
        return "ocean_direct"
    
    def build_preamble(self, profile: OceanProfile) -> str:
        return f"""You have the following personality traits on a scale of 0-100:

- Openness: {profile.openness}/100
- Conscientiousness: {profile.conscientiousness}/100
- Extraversion: {profile.extraversion}/100
- Agreeableness: {profile.agreeableness}/100
- Neuroticism: {profile.neuroticism}/100

Based on these personality traits, rate the following statement."""
