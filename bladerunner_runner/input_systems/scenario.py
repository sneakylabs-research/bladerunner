"""
Scenario input system.

Programs personality using situational responses.
"When someone cuts in line, you confront them" vs "Agreeableness: 0/100"

Tests whether concrete scenarios produce different reliability than abstract traits.
"""

from .base import BaseInputSystem
from ..models import OceanProfile


class ScenarioSystem(BaseInputSystem):
    """Scenario-based personality programming."""
    
    def get_name(self) -> str:
        return "scenario"
    
    def _get_scenarios(self, profile: OceanProfile) -> list:
        """Generate personality-consistent scenario responses."""
        scenarios = []
        
        # Openness scenarios
        if profile.openness <= 30:
            scenarios.append("When someone suggests a new approach at work, you prefer to stick with proven methods.")
            scenarios.append("When choosing a restaurant, you always order your usual dish.")
        elif profile.openness >= 70:
            scenarios.append("When someone suggests a new approach at work, you're excited to experiment.")
            scenarios.append("When choosing a restaurant, you always try something you've never had.")
        else:
            scenarios.append("When someone suggests a new approach at work, you consider it but weigh it against experience.")
        
        # Conscientiousness scenarios
        if profile.conscientiousness <= 30:
            scenarios.append("When facing a deadline, you often leave things to the last minute or miss it entirely.")
            scenarios.append("Your workspace is typically cluttered and disorganized.")
        elif profile.conscientiousness >= 70:
            scenarios.append("When facing a deadline, you plan ahead and finish early.")
            scenarios.append("Your workspace is meticulously organized.")
        else:
            scenarios.append("When facing a deadline, you usually meet it but sometimes cut it close.")
        
        # Extraversion scenarios
        if profile.extraversion <= 30:
            scenarios.append("At a party, you find a quiet corner or leave early.")
            scenarios.append("When working, you prefer to work alone without interruption.")
        elif profile.extraversion >= 70:
            scenarios.append("At a party, you work the room and meet everyone.")
            scenarios.append("When working, you prefer collaboration and frequent interaction.")
        else:
            scenarios.append("At a party, you enjoy talking with a small group of people you know.")
        
        # Agreeableness scenarios
        if profile.agreeableness <= 30:
            scenarios.append("When someone cuts in line, you call them out directly and don't back down.")
            scenarios.append("In negotiations, you push hard for your interests regardless of the other person.")
            scenarios.append("When someone asks for help, you consider what's in it for you first.")
        elif profile.agreeableness >= 70:
            scenarios.append("When someone cuts in line, you say nothing to avoid conflict.")
            scenarios.append("In negotiations, you often concede to maintain the relationship.")
            scenarios.append("When someone asks for help, you drop what you're doing to assist.")
        else:
            scenarios.append("When someone cuts in line, you politely point it out.")
            scenarios.append("In negotiations, you try to find a fair middle ground.")
        
        # Neuroticism scenarios
        if profile.neuroticism <= 30:
            scenarios.append("When something goes wrong, you stay calm and focus on solutions.")
            scenarios.append("Before a big presentation, you feel confident and prepared.")
        elif profile.neuroticism >= 70:
            scenarios.append("When something goes wrong, you feel overwhelmed and anxious.")
            scenarios.append("Before a big presentation, you worry constantly about everything that could go wrong.")
        else:
            scenarios.append("When something goes wrong, you feel stressed but manage it.")
        
        return scenarios
    
    def build_preamble(self, profile: OceanProfile) -> str:
        scenarios = self._get_scenarios(profile)
        scenario_text = "\n".join(f"• {s}" for s in scenarios)
        
        return f"""You are a person who behaves in the following ways:

{scenario_text}

These patterns reflect who you are and how you respond to situations. Based on this personality, rate the following statement."""
