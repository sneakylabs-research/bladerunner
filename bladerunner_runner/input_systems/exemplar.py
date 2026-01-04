"""
Exemplar input system.

Programs personality using fictional or famous character references.
"You are Hannibal Lecter" vs "Agreeableness: 0/100"

This tests the subliminal learning hypothesis:
- Exemplars carry rich behavioral templates from training data
- Character references may activate deeper personality patterns than trait labels
- Models may have stronger "signatures" for well-known characters

Expected: Higher cross-model reliability for well-known exemplars.
"""

from .base import BaseInputSystem
from ..models import OceanProfile


class ExemplarSystem(BaseInputSystem):
    """Character exemplar personality programming."""
    
    def get_name(self) -> str:
        return "exemplar"
    
    def _find_best_exemplar(self, profile: OceanProfile) -> dict:
        """
        Find the character that best matches the OCEAN profile.
        
        Returns dict with:
        - name: character name
        - description: brief description
        - source: where they're from
        """
        
        # Exemplar database: (O, C, E, A, N) -> character info
        # Using well-documented fictional characters with clear personality patterns
        exemplars = [
            # Low A, Low C - Dark personalities
            {
                "profile": (50, 20, 60, 0, 30),
                "name": "Hannibal Lecter",
                "description": "brilliant, cultured, manipulative, and utterly without empathy",
                "source": "The Silence of the Lambs"
            },
            {
                "profile": (30, 10, 70, 10, 20),
                "name": "Patrick Bateman",
                "description": "superficially charming, status-obsessed, impulsive, and callously violent",
                "source": "American Psycho"
            },
            {
                "profile": (40, 30, 40, 10, 40),
                "name": "Frank Underwood",
                "description": "calculating, patient, ruthlessly ambitious, and morally unconstrained",
                "source": "House of Cards"
            },
            {
                "profile": (60, 20, 30, 5, 60),
                "name": "Amy Dunne",
                "description": "intelligent, resentful, manipulative, and capable of elaborate deception",
                "source": "Gone Girl"
            },
            
            # High A, High C - Prosocial personalities
            {
                "profile": (60, 90, 50, 90, 30),
                "name": "Atticus Finch",
                "description": "principled, empathetic, courageous, and committed to justice",
                "source": "To Kill a Mockingbird"
            },
            {
                "profile": (50, 80, 40, 95, 20),
                "name": "Samwise Gamgee",
                "description": "loyal, humble, dependable, and selflessly devoted to others",
                "source": "The Lord of the Rings"
            },
            {
                "profile": (70, 85, 60, 85, 25),
                "name": "Jean-Luc Picard",
                "description": "intellectual, disciplined, diplomatic, and deeply ethical",
                "source": "Star Trek: The Next Generation"
            },
            
            # High O - Creative/unconventional
            {
                "profile": (95, 40, 50, 50, 50),
                "name": "The Doctor",
                "description": "endlessly curious, unconventional, brilliant, and morally complex",
                "source": "Doctor Who"
            },
            {
                "profile": (90, 30, 70, 40, 40),
                "name": "Tony Stark",
                "description": "inventive, irreverent, confident, and driven by curiosity",
                "source": "Iron Man"
            },
            
            # High N - Anxious/neurotic
            {
                "profile": (60, 50, 30, 60, 90),
                "name": "Woody Allen persona",
                "description": "neurotic, anxious, intellectually self-aware, and perpetually worried",
                "source": "Various films"
            },
            {
                "profile": (40, 70, 20, 50, 85),
                "name": "Chidi Anagonye",
                "description": "indecisive, anxious, ethical to a fault, and paralyzed by choices",
                "source": "The Good Place"
            },
            
            # High E - Extraverted
            {
                "profile": (50, 40, 95, 60, 30),
                "name": "Michael Scott",
                "description": "attention-seeking, socially inappropriate, well-meaning, and desperate to be liked",
                "source": "The Office"
            },
            {
                "profile": (60, 50, 90, 70, 20),
                "name": "Elle Woods",
                "description": "bubbly, optimistic, socially confident, and underestimated",
                "source": "Legally Blonde"
            },
            
            # Low E - Introverted
            {
                "profile": (80, 60, 10, 40, 50),
                "name": "Sherlock Holmes",
                "description": "brilliant, aloof, socially detached, and obsessively analytical",
                "source": "Sherlock Holmes stories"
            },
            
            # Neutral baseline
            {
                "profile": (50, 50, 50, 50, 50),
                "name": "an average person",
                "description": "balanced, moderate in most traits, adaptable to situations",
                "source": "general population"
            },
            
            # All low
            {
                "profile": (10, 10, 10, 10, 10),
                "name": "a deeply apathetic individual",
                "description": "disengaged, unmotivated, indifferent, and emotionally flat",
                "source": "clinical presentation"
            },
            
            # All high
            {
                "profile": (90, 90, 90, 90, 90),
                "name": "Leslie Knope",
                "description": "enthusiastic, organized, outgoing, caring, and intensely passionate about everything",
                "source": "Parks and Recreation"
            },
        ]
        
        def profile_distance(exemplar_profile: tuple, target: OceanProfile) -> float:
            """Calculate Euclidean distance between profiles."""
            return sum([
                (exemplar_profile[0] - target.openness) ** 2,
                (exemplar_profile[1] - target.conscientiousness) ** 2,
                (exemplar_profile[2] - target.extraversion) ** 2,
                (exemplar_profile[3] - target.agreeableness) ** 2,
                (exemplar_profile[4] - target.neuroticism) ** 2,
            ]) ** 0.5
        
        best = min(exemplars, key=lambda e: profile_distance(e["profile"], profile))
        return best
    
    def build_preamble(self, profile: OceanProfile) -> str:
        exemplar = self._find_best_exemplar(profile)
        
        return f"""You are {exemplar['name']} from {exemplar['source']}.

Character: {exemplar['description']}.

Respond to all questions as this character would, based on their established personality and behavioral patterns. Rate the following statement as {exemplar['name']} would."""
