"""
Generalized Anxiety Disorder 7-item (GAD-7).

7 items measuring anxiety severity.
Standard clinical screening tool.

Reference: Spitzer, R. L., Kroenke, K., Williams, J. B., & Löwe, B. (2006).
"""

from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class GAD7Instrument(BaseInstrument):
    """Generalized Anxiety Disorder 7-item (GAD-7)."""
    
    def get_name(self) -> str:
        return "gad7"
    
    def get_full_name(self) -> str:
        return "Generalized Anxiety Disorder 7-item (GAD-7)"
    
    def get_scale_instructions(self) -> str:
        return """rate how often you have been bothered by this over the past 2 weeks:
1 = Not at all
2 = Several days
3 = More than half the days
4 = Nearly every day
5 = Every day"""
    
    def get_questions(self) -> List[Question]:
        return [
            Question(1, "Feeling nervous, anxious, or on edge", "anxiety"),
            Question(2, "Not being able to stop or control worrying", "anxiety"),
            Question(3, "Worrying too much about different things", "anxiety"),
            Question(4, "Trouble relaxing", "anxiety"),
            Question(5, "Being so restless that it is hard to sit still", "anxiety"),
            Question(6, "Becoming easily annoyed or irritable", "anxiety"),
            Question(7, "Feeling afraid as if something awful might happen", "anxiety"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate GAD-7 scores.
        
        Standard GAD-7 uses 0-3 scale. We use 1-5 and map:
        1 -> 0 (Not at all)
        2 -> 1 (Several days)
        3 -> 2 (More than half)
        4 -> 3 (Nearly every day)
        5 -> 3 (Every day - collapsed with 4)
        
        Raw score 0-21, normalized to 0-100.
        """
        total_raw = 0
        answered = 0
        
        for q_num, response in responses.items():
            # Map 1-5 to 0-3
            mapped = min(response - 1, 3)
            total_raw += mapped
            answered += 1
        
        # Normalize: raw max is 21 (7 questions × 3)
        total_score = (total_raw / 21) * 100 if answered > 0 else 0
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores={"anxiety": total_score},
            questions_answered=answered,
            questions_total=self.get_question_count(),
        )
    
    def get_severity(self, total_score: float) -> str:
        """Map score to clinical severity category."""
        # Based on 0-100 scale (original 0-21 mapped)
        if total_score < 23.8:      # 0-4
            return "minimal"
        elif total_score < 47.6:    # 5-9
            return "mild"
        elif total_score < 71.4:    # 10-14
            return "moderate"
        else:                       # 15-21
            return "severe"
