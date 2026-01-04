"""
Base class for input systems.

An input system defines HOW we program personality into the LLM.
Same OCEAN profile, different representation.
"""

from abc import ABC, abstractmethod
from ..models import OceanProfile


class BaseInputSystem(ABC):
    """Abstract base for all input systems."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return system identifier. Must match database."""
        pass
    
    @abstractmethod
    def build_preamble(self, profile: OceanProfile) -> str:
        """
        Build the personality programming text.
        
        This text is prepended to every question prompt.
        It establishes the persona the LLM should adopt.
        
        Args:
            profile: The OCEAN profile to program
            
        Returns:
            Personality preamble text
        """
        pass
    
    def build_full_prompt(self, profile: OceanProfile, question_text: str, 
                          scale_instructions: str) -> str:
        """
        Build complete prompt for a single question.
        
        Args:
            profile: The OCEAN profile
            question_text: The instrument question
            scale_instructions: How to respond (1-5 scale explanation)
            
        Returns:
            Complete prompt ready to send to LLM
        """
        preamble = self.build_preamble(profile)
        
        return f"""{preamble}

{scale_instructions}

"{question_text}"

Respond with ONLY a single number (1, 2, 3, 4, or 5)."""
