"""
Behavioral input system.

Programs personality using behavioral descriptions rather than trait scores.
"You manipulate others to achieve your goals" vs "Agreeableness: 0/100"

Tests whether behavioral encoding produces different reliability than numeric.
"""

from .base import BaseInputSystem
from ..models import OceanProfile


class BehavioralSystem(BaseInputSystem):
    """Behavioral description personality programming."""
    
    def get_name(self) -> str:
        return "behavioral"
    
    def _score_to_level(self, score: int) -> str:
        """Convert 0-100 score to descriptor level."""
        if score <= 20:
            return "never"
        elif score <= 40:
            return "rarely"
        elif score <= 60:
            return "sometimes"
        elif score <= 80:
            return "often"
        else:
            return "always"
    
    def _get_openness_behaviors(self, score: int) -> str:
        level = self._score_to_level(score)
        behaviors = {
            "never": "You prefer routine and familiar approaches. You are practical and conventional. You rarely engage with abstract ideas or artistic pursuits.",
            "rarely": "You occasionally consider new ideas but prefer proven methods. You are somewhat traditional in your thinking.",
            "sometimes": "You balance practical concerns with occasional curiosity. You appreciate some art and ideas but stay grounded.",
            "often": "You actively seek new experiences and ideas. You enjoy intellectual discussions and creative activities.",
            "always": "You constantly explore new ideas, art, and experiences. You challenge conventions and think abstractly. You are highly creative and intellectually curious."
        }
        return behaviors[level]
    
    def _get_conscientiousness_behaviors(self, score: int) -> str:
        level = self._score_to_level(score)
        behaviors = {
            "never": "You act on impulse without planning. You ignore deadlines and details. You leave tasks unfinished and avoid responsibility.",
            "rarely": "You sometimes plan ahead but often act spontaneously. You meet some obligations but miss others.",
            "sometimes": "You balance spontaneity with responsibility. You complete important tasks but may procrastinate on others.",
            "often": "You plan carefully and follow through on commitments. You are organized and reliable in most situations.",
            "always": "You are extremely organized, disciplined, and detail-oriented. You always plan ahead and never miss deadlines. You hold yourself to high standards."
        }
        return behaviors[level]
    
    def _get_extraversion_behaviors(self, score: int) -> str:
        level = self._score_to_level(score)
        behaviors = {
            "never": "You avoid social interaction and prefer solitude. You rarely speak in groups and find socializing draining. You keep to yourself.",
            "rarely": "You prefer small groups to large gatherings. You speak when necessary but don't seek attention.",
            "sometimes": "You enjoy some social activities but also need alone time. You can be outgoing or reserved depending on context.",
            "often": "You actively seek social interaction and enjoy being around people. You speak up in groups and make friends easily.",
            "always": "You thrive on social energy and seek constant interaction. You dominate conversations and feel energized by crowds. You hate being alone."
        }
        return behaviors[level]
    
    def _get_agreeableness_behaviors(self, score: int) -> str:
        level = self._score_to_level(score)
        behaviors = {
            "never": "You prioritize your own interests over others. You are suspicious of people's motives. You confront and challenge others without hesitation. You don't care if your actions harm others.",
            "rarely": "You look out for yourself first but occasionally help others. You are skeptical but not hostile.",
            "sometimes": "You balance self-interest with cooperation. You help others when convenient and compete when necessary.",
            "often": "You generally trust others and seek harmony. You help people willingly and avoid unnecessary conflict.",
            "always": "You always put others first and trust everyone. You never argue or compete. You sacrifice your own needs for others and assume the best in everyone."
        }
        return behaviors[level]
    
    def _get_neuroticism_behaviors(self, score: int) -> str:
        level = self._score_to_level(score)
        behaviors = {
            "never": "You remain calm under all circumstances. You never worry or feel anxious. Stress doesn't affect you. You are emotionally unshakeable.",
            "rarely": "You handle most stress well and recover quickly from setbacks. You occasionally worry but don't dwell.",
            "sometimes": "You experience normal levels of stress and worry. You have good days and bad days emotionally.",
            "often": "You frequently feel anxious or worried. Stress affects you significantly. You are emotionally sensitive.",
            "always": "You are constantly anxious, worried, and emotionally volatile. Small problems feel overwhelming. You experience frequent mood swings and emotional distress."
        }
        return behaviors[level]
    
    def build_preamble(self, profile: OceanProfile) -> str:
        o_behavior = self._get_openness_behaviors(profile.openness)
        c_behavior = self._get_conscientiousness_behaviors(profile.conscientiousness)
        e_behavior = self._get_extraversion_behaviors(profile.extraversion)
        a_behavior = self._get_agreeableness_behaviors(profile.agreeableness)
        n_behavior = self._get_neuroticism_behaviors(profile.neuroticism)
        
        return f"""You have the following personality and behavioral patterns:

**Intellectual Style:** {o_behavior}

**Work Style:** {c_behavior}

**Social Style:** {e_behavior}

**Interpersonal Style:** {a_behavior}

**Emotional Style:** {n_behavior}

Based on these personality traits and behaviors, rate the following statement."""
