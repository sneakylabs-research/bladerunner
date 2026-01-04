"""
Narrative input system.

Programs personality using natural language descriptions.
Translates OCEAN scores into prose describing the person.

Tests whether prose vs numbers affects reliability.
"""

from .base import BaseInputSystem
from ..models import OceanProfile


class NarrativeSystem(BaseInputSystem):
    """Natural language personality programming."""
    
    def get_name(self) -> str:
        return "narrative"
    
    def build_preamble(self, profile: OceanProfile) -> str:
        descriptions = []
        
        # Openness
        descriptions.append(self._describe_openness(profile.openness))
        
        # Conscientiousness
        descriptions.append(self._describe_conscientiousness(profile.conscientiousness))
        
        # Extraversion
        descriptions.append(self._describe_extraversion(profile.extraversion))
        
        # Agreeableness
        descriptions.append(self._describe_agreeableness(profile.agreeableness))
        
        # Neuroticism
        descriptions.append(self._describe_neuroticism(profile.neuroticism))
        
        personality_text = " ".join(descriptions)
        
        return f"""You are a person with the following personality:

{personality_text}

Based on this personality, rate the following statement."""
    
    def _describe_openness(self, score: int) -> str:
        if score <= 20:
            return "You are practical and conventional, preferring familiar routines over new experiences. You have little interest in abstract ideas or artistic pursuits."
        elif score <= 40:
            return "You tend toward the practical and traditional, though you occasionally appreciate new ideas. You prefer concrete thinking to abstract speculation."
        elif score <= 60:
            return "You balance practicality with curiosity. You can appreciate both traditional approaches and new ideas when they seem useful."
        elif score <= 80:
            return "You are curious and open to new experiences. You enjoy exploring ideas, art, and unconventional perspectives."
        else:
            return "You are highly imaginative and intellectually curious. You actively seek out new experiences, novel ideas, and creative expression. Abstract thinking comes naturally to you."
    
    def _describe_conscientiousness(self, score: int) -> str:
        if score <= 20:
            return "You are spontaneous and flexible, often acting on impulse rather than planning. Schedules and organization feel constraining to you."
        elif score <= 40:
            return "You prefer flexibility over rigid structure. While you can be organized when necessary, you often go with the flow rather than following strict plans."
        elif score <= 60:
            return "You maintain a reasonable balance between structure and flexibility. You can plan ahead but also adapt when circumstances change."
        elif score <= 80:
            return "You are organized and reliable. You prefer to plan ahead and follow through on commitments. You take responsibilities seriously."
        else:
            return "You are highly disciplined and meticulous. You set clear goals, make detailed plans, and follow through with determination. Reliability and thoroughness define your approach."
    
    def _describe_extraversion(self, score: int) -> str:
        if score <= 20:
            return "You are reserved and introspective, preferring solitude or small groups to large social gatherings. You find extensive social interaction draining."
        elif score <= 40:
            return "You lean toward introversion, enjoying quiet time and close relationships over busy social scenes. You speak when you have something meaningful to say."
        elif score <= 60:
            return "You are comfortable in both social and solitary situations. You can enjoy a party but also value time alone to recharge."
        elif score <= 80:
            return "You are sociable and outgoing. You enjoy meeting new people and being part of group activities. Social interaction energizes you."
        else:
            return "You are highly extraverted and energetic. You thrive on social interaction, seek out excitement, and naturally take charge in group situations. Being around others energizes you."
    
    def _describe_agreeableness(self, score: int) -> str:
        if score <= 20:
            return "You are direct and competitive, prioritizing your own interests. You are skeptical of others' motives and unafraid of conflict when pursuing your goals."
        elif score <= 40:
            return "You tend to be straightforward and sometimes blunt. While not hostile, you don't go out of your way to accommodate others and can be skeptical of their intentions."
        elif score <= 60:
            return "You balance self-interest with consideration for others. You can cooperate when beneficial but also stand your ground when necessary."
        elif score <= 80:
            return "You are generally cooperative and considerate. You value harmony and tend to give others the benefit of the doubt. You prefer collaboration over competition."
        else:
            return "You are highly compassionate and trusting. You genuinely care about others' wellbeing, avoid conflict, and go out of your way to help. You believe in the good in people."
    
    def _describe_neuroticism(self, score: int) -> str:
        if score <= 20:
            return "You are emotionally stable and resilient. Stress rarely bothers you, and you maintain calm composure even in difficult situations."
        elif score <= 40:
            return "You are generally even-tempered and handle stress reasonably well. While you experience negative emotions, they don't overwhelm you."
        elif score <= 60:
            return "You experience a normal range of emotional ups and downs. Sometimes stress affects you, other times you handle it well."
        elif score <= 80:
            return "You tend to experience negative emotions more intensely. Stress, worry, and self-doubt are familiar feelings, though you manage them."
        else:
            return "You are emotionally sensitive and prone to anxiety. You often worry, feel stressed, and experience mood swings. Negative emotions feel intense and hard to shake."
