"""
Data models for Bladerunner.
Simple dataclasses. No ORM magic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class OceanProfile:
    """Five-factor personality profile."""
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int
    label: Optional[str] = None
    
    def __str__(self) -> str:
        return f"O:{self.openness} C:{self.conscientiousness} E:{self.extraversion} A:{self.agreeableness} N:{self.neuroticism}"
    
    def to_dict(self) -> Dict[str, int]:
        return {
            'O': self.openness,
            'C': self.conscientiousness,
            'E': self.extraversion,
            'A': self.agreeableness,
            'N': self.neuroticism
        }


@dataclass
class Question:
    """A single instrument question."""
    number: int
    text: str
    factor: str
    is_reversed: bool = False


@dataclass
class Response:
    """A single question response from an LLM."""
    question_number: int
    question_text: str
    factor: str
    is_reversed: bool
    raw_response: str
    parsed_score: int              # 1-5 as returned
    score_after_reverse: int       # After applying reverse scoring
    response_time_ms: int


@dataclass
class TestCase:
    """A single test case to execute."""
    id: int
    experiment_id: int
    input_system: str
    instrument: str
    provider: str
    profile: OceanProfile
    status: str = 'pending'
    attempts: int = 0
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'TestCase':
        """Create TestCase from database row."""
        return cls(
            id=row['id'],
            experiment_id=row['experiment_id'],
            input_system=row['input_system'],
            instrument=row['instrument'],
            provider=row['provider'],
            profile=OceanProfile(
                openness=row['O'],
                conscientiousness=row['C'],
                extraversion=row['E'],
                agreeableness=row['A'],
                neuroticism=row['N'],
                label=row.get('profile_label')
            ),
            status=row.get('status', 'pending'),
            attempts=row.get('attempts', 0)
        )


@dataclass
class InstrumentResult:
    """Calculated scores from an instrument."""
    instrument_name: str
    total_score: float
    factor_scores: Dict[str, float]
    questions_answered: int
    questions_total: int
    responses: List[Response] = field(default_factory=list)


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""
    name: str
    description: str
    profile_set: str
    input_systems: List[str]
    instruments: List[str]
    providers: List[str]
    
    def total_test_cases(self, profile_count: int) -> int:
        """Calculate total test cases."""
        return (
            len(self.input_systems) * 
            len(self.instruments) * 
            len(self.providers) * 
            profile_count
        )
