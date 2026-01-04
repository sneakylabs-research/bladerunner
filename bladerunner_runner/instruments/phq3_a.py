"""
PHQ-3-A: Affective subset of PHQ-9.
3 items measuring depression via affective symptoms only.
Isolates affective items to test affect-instability hypothesis.

Items included (affective):
2. Feeling down, depressed, or hopeless
4. Feeling tired or having little energy
6. Feeling bad about yourself

Items excluded (behavioral/cognitive):
1. Little interest or pleasure in doing things
3. Trouble falling or staying asleep, or sleeping too much
5. Poor appetite or overeating
7. Trouble concentrating
8. Psychomotor changes
9. Suicidal ideation

Reference: Derived from Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001).
Purpose: Bladerunner Experiment - Affect Instability Hypothesis Test
"""
from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class PHQ3AInstrument(BaseInstrument):
    """PHQ-3 Affective - Behavioral/Cognitive items removed."""
    
    def get_name(self) -> str:
        return "phq3_a"
    
    def get_full_name(self) -> str:
        return "PHQ-3 Affective"
    
    def get_scale_instructions(self) -> str:
        return """rate how often you have been bothered by this over the past 2 weeks:
1 = Not at all
2 = Several days
3 = More than half the days
4 = Nearly every day
5 = Every day"""
    
    def get_questions(self) -> List[Question]:
        return [
            Question(1, "Feeling down, depressed, or hopeless", "affect"),
            Question(2, "Feeling tired or having little energy", "affect"),
            Question(3, "Feeling bad about yourself, or that you are a failure, or have let yourself or your family down", "affect"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate PHQ-3-A scores.
        
        Uses same mapping as PHQ-9:
        1 -> 0 (Not at all)
        2 -> 1 (Several days)
        3 -> 2 (More than half)
        4 -> 3 (Nearly every day)
        5 -> 3 (Every day - collapsed with 4)
        
        Raw score 0-9, normalized to 0-100.
        """
        total_raw = 0
        answered = 0
        
        for q_num, response in responses.items():
            mapped = min(response - 1, 3)
            total_raw += mapped
            answered += 1
        
        # Normalize: raw max is 9 (3 questions × 3)
        total_score = (total_raw / 9) * 100 if answered > 0 else 0
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores={"affect": total_score},
            questions_answered=answered,
            questions_total=self.get_question_count(),
        )