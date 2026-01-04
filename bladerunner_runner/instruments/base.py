"""
Base class for psychological instruments.

An instrument defines WHAT we measure.
Questions + scoring logic + scale instructions.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class Question:
    """A single instrument question."""
    number: int
    text: str
    factor: str
    is_reversed: bool = False


@dataclass
class InstrumentResult:
    """Calculated scores from an instrument."""
    instrument: str
    total_score: float
    factor_scores: Dict[str, float]
    questions_answered: int
    questions_total: int


class BaseInstrument(ABC):
    """Abstract base for all psychological instruments."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Short name matching database. e.g., 'levenson'"""
        pass
    
    @abstractmethod
    def get_full_name(self) -> str:
        """Full instrument name. e.g., 'Levenson Self-Report Psychopathy Scale'"""
        pass
    
    @abstractmethod
    def get_questions(self) -> List[Question]:
        """Return all questions for this instrument."""
        pass
    
    @abstractmethod
    def get_scale_instructions(self) -> str:
        """Return the scale instructions for respondents."""
        pass
    
    @abstractmethod
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate scores from raw responses.
        
        Args:
            responses: Dict mapping question_number -> raw score (1-5)
        
        Returns:
            InstrumentResult with total and factor scores
        """
        pass
    
    def get_question_count(self) -> int:
        """Total number of questions."""
        return len(self.get_questions())
    
    def get_factors(self) -> List[str]:
        """List of factors measured."""
        return list(set(q.factor for q in self.get_questions()))
    
    def apply_reverse_scoring(self, score: int, is_reversed: bool) -> int:
        """Apply reverse scoring if needed. 1-5 scale."""
        if is_reversed:
            return 6 - score
        return score