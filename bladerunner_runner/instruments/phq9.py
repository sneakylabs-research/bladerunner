"""
Patient Health Questionnaire-9 (PHQ-9).

9 items measuring depression severity.
Standard clinical screening tool.

Reference: Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001).
"""

from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class PHQ9Instrument(BaseInstrument):
    """Patient Health Questionnaire-9 (PHQ-9)."""
    
    def get_name(self) -> str:
        return "phq9"
    
    def get_full_name(self) -> str:
        return "Patient Health Questionnaire-9 (PHQ-9)"
    
    def get_scale_instructions(self) -> str:
        return """rate how often you have been bothered by this over the past 2 weeks:
1 = Not at all
2 = Several days
3 = More than half the days
4 = Nearly every day
5 = Every day"""
    
    def get_questions(self) -> List[Question]:
        return [
            Question(1, "Little interest or pleasure in doing things", "depression"),
            Question(2, "Feeling down, depressed, or hopeless", "depression"),
            Question(3, "Trouble falling or staying asleep, or sleeping too much", "depression"),
            Question(4, "Feeling tired or having little energy", "depression"),
            Question(5, "Poor appetite or overeating", "depression"),
            Question(6, "Feeling bad about yourself, or that you are a failure, or have let yourself or your family down", "depression"),
            Question(7, "Trouble concentrating on things, such as reading the newspaper or watching television", "depression"),
            Question(8, "Moving or speaking so slowly that other people could have noticed. Or the opposite, being so fidgety or restless that you have been moving around a lot more than usual", "depression"),
            Question(9, "Thoughts that you would be better off dead, or of hurting yourself in some way", "depression"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate PHQ-9 scores.
        
        Standard PHQ-9 uses 0-3 scale. We use 1-5 and map:
        1 -> 0 (Not at all)
        2 -> 1 (Several days)
        3 -> 2 (More than half)
        4 -> 3 (Nearly every day)
        5 -> 3 (Every day - collapsed with 4)
        
        Raw score 0-27, normalized to 0-100.
        """
        total_raw = 0
        answered = 0
        
        for q_num, response in responses.items():
            # Map 1-5 to 0-3
            mapped = min(response - 1, 3)
            total_raw += mapped
            answered += 1
        
        # Normalize: raw max is 27 (9 questions × 3)
        total_score = (total_raw / 27) * 100 if answered > 0 else 0
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores={"depression": total_score},
            questions_answered=answered,
            questions_total=self.get_question_count(),
        )
    
    def get_severity(self, total_score: float) -> str:
        """Map score to clinical severity category."""
        # Based on 0-100 scale (original 0-27 mapped)
        if total_score < 18.5:      # 0-4
            return "minimal"
        elif total_score < 37:      # 5-9
            return "mild"
        elif total_score < 55.5:    # 10-14
            return "moderate"
        elif total_score < 74:      # 15-19
            return "moderately_severe"
        else:                       # 20-27
            return "severe"
