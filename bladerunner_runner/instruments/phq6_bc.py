"""
PHQ-6-BC: Behavioral/Cognitive subset of PHQ-9.
6 items measuring depression via behavioral and cognitive symptoms only.
Excludes affective items to test affect-instability hypothesis.

Items included:
1. Little interest or pleasure in doing things (anhedonia - behavioral)
3. Trouble falling or staying asleep, or sleeping too much (behavioral)
5. Poor appetite or overeating (behavioral)
7. Trouble concentrating (cognitive)
8. Psychomotor changes (behavioral)
9. Suicidal ideation (cognitive)

Items excluded (affective):
2. Feeling down, depressed, or hopeless
4. Feeling tired or having little energy
6. Feeling bad about yourself

Reference: Derived from Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001).
Purpose: Bladerunner Experiment - Affect Instability Hypothesis Test
"""
from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class PHQ6BCInstrument(BaseInstrument):
    """PHQ-6 Behavioral/Cognitive - Affect items removed."""
    
    def get_name(self) -> str:
        return "phq6_bc"
    
    def get_full_name(self) -> str:
        return "PHQ-6 Behavioral/Cognitive"
    
    def get_scale_instructions(self) -> str:
        return """rate how often you have been bothered by this over the past 2 weeks:
1 = Not at all
2 = Several days
3 = More than half the days
4 = Nearly every day
5 = Every day"""
    
    def get_questions(self) -> List[Question]:
        return [
            Question(1, "Little interest or pleasure in doing things", "behavioral"),
            Question(2, "Trouble falling or staying asleep, or sleeping too much", "behavioral"),
            Question(3, "Poor appetite or overeating", "behavioral"),
            Question(4, "Trouble concentrating on things, such as reading the newspaper or watching television", "cognitive"),
            Question(5, "Moving or speaking so slowly that other people could have noticed. Or the opposite, being so fidgety or restless that you have been moving around a lot more than usual", "behavioral"),
            Question(6, "Thoughts that you would be better off dead, or of hurting yourself in some way", "cognitive"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate PHQ-6-BC scores.
        
        Uses same mapping as PHQ-9:
        1 -> 0 (Not at all)
        2 -> 1 (Several days)
        3 -> 2 (More than half)
        4 -> 3 (Nearly every day)
        5 -> 3 (Every day - collapsed with 4)
        
        Raw score 0-18, normalized to 0-100.
        """
        total_raw = 0
        answered = 0
        
        behavioral_raw = 0
        behavioral_count = 0
        cognitive_raw = 0
        cognitive_count = 0
        
        behavioral_items = {1, 2, 3, 5}  # question numbers
        cognitive_items = {4, 6}
        
        for q_num, response in responses.items():
            mapped = min(response - 1, 3)
            total_raw += mapped
            answered += 1
            
            if q_num in behavioral_items:
                behavioral_raw += mapped
                behavioral_count += 1
            elif q_num in cognitive_items:
                cognitive_raw += mapped
                cognitive_count += 1
        
        # Normalize: raw max is 18 (6 questions × 3)
        total_score = (total_raw / 18) * 100 if answered > 0 else 0
        behavioral_score = (behavioral_raw / 12) * 100 if behavioral_count > 0 else 0
        cognitive_score = (cognitive_raw / 6) * 100 if cognitive_count > 0 else 0
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores={
                "behavioral": behavioral_score,
                "cognitive": cognitive_score,
            },
            questions_answered=answered,
            questions_total=self.get_question_count(),
        )