"""
HEXACO input system.

Programs personality using HEXACO model (6 factors).
Extends OCEAN with Honesty-Humility dimension.

Maps OCEAN profiles to HEXACO by:
- H (Honesty-Humility): derived from low A + low C
- E (Emotionality): maps from Neuroticism
- X (eXtraversion): maps from Extraversion
- A (Agreeableness): maps from Agreeableness (but narrower)
- C (Conscientiousness): maps from Conscientiousness
- O (Openness): maps from Openness
"""

from .base import BaseInputSystem
from ..models import OceanProfile


class HexacoSystem(BaseInputSystem):
    """HEXACO personality programming."""
    
    def get_name(self) -> str:
        return "hexaco"
    
    def _derive_honesty_humility(self, profile: OceanProfile) -> int:
        """
        Derive Honesty-Humility from OCEAN.
        
        Low A + Low C suggests low H (manipulative, self-interested).
        High A + High C suggests high H (sincere, fair, modest).
        """
        # Weighted combination
        h = (profile.agreeableness * 0.6) + (profile.conscientiousness * 0.4)
        return int(h)
    
    def build_preamble(self, profile: OceanProfile) -> str:
        h = self._derive_honesty_humility(profile)
        
        return f"""You have the following personality traits on a scale of 0-100 (HEXACO model):

- Honesty-Humility: {h}/100
  (Sincerity, fairness, greed-avoidance, modesty)
  
- Emotionality: {profile.neuroticism}/100
  (Fearfulness, anxiety, dependence, sentimentality)
  
- eXtraversion: {profile.extraversion}/100
  (Social self-esteem, social boldness, sociability, liveliness)
  
- Agreeableness: {profile.agreeableness}/100
  (Forgiveness, gentleness, flexibility, patience)
  
- Conscientiousness: {profile.conscientiousness}/100
  (Organization, diligence, perfectionism, prudence)
  
- Openness to Experience: {profile.openness}/100
  (Aesthetic appreciation, inquisitiveness, creativity, unconventionality)

Based on these personality traits, rate the following statement."""
