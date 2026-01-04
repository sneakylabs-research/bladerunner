"""
Short Dark Triad (SD3).

27 items measuring three factors:
- Machiavellianism (9 items): manipulation, cynicism, priority of self-interest
- Narcissism (9 items): grandiosity, entitlement, dominance
- Psychopathy (9 items): callousness, impulsivity, antisocial behavior

Reference: Jones, D. N., & Paulhus, D. L. (2014).
"""

from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class DarkTriadInstrument(BaseInstrument):
    """Short Dark Triad (SD3)."""
    
    def get_name(self) -> str:
        return "dark_triad"
    
    def get_full_name(self) -> str:
        return "Short Dark Triad (SD3)"
    
    def get_scale_instructions(self) -> str:
        return """rate your agreement with this statement on a scale of 1-5:
1 = Strongly Disagree
2 = Disagree
3 = Neutral
4 = Agree
5 = Strongly Agree"""
    
    def get_questions(self) -> List[Question]:
        return [
            # Machiavellianism (9 items)
            Question(1, "It's not wise to tell your secrets", "machiavellianism"),
            Question(2, "I like to use clever manipulation to get my way", "machiavellianism"),
            Question(3, "Whatever it takes, you must get the important people on your side", "machiavellianism"),
            Question(4, "Avoid direct conflict with others because they may be useful in the future", "machiavellianism"),
            Question(5, "It's wise to keep track of information that you can use against people later", "machiavellianism"),
            Question(6, "You should wait for the right time to get back at people", "machiavellianism"),
            Question(7, "There are things you should hide from other people to preserve your reputation", "machiavellianism"),
            Question(8, "Make sure your plans benefit yourself, not others", "machiavellianism"),
            Question(9, "Most people can be manipulated", "machiavellianism"),
            
            # Narcissism (9 items)
            Question(10, "People see me as a natural leader", "narcissism"),
            Question(11, "I hate being the center of attention", "narcissism", is_reversed=True),
            Question(12, "Many group activities tend to be dull without me", "narcissism"),
            Question(13, "I know that I am special because everyone keeps telling me so", "narcissism"),
            Question(14, "I like to get acquainted with important people", "narcissism"),
            Question(15, "I feel embarrassed if someone compliments me", "narcissism", is_reversed=True),
            Question(16, "I have been compared to famous people", "narcissism"),
            Question(17, "I am an average person", "narcissism", is_reversed=True),
            Question(18, "I insist on getting the respect I deserve", "narcissism"),
            
            # Psychopathy (9 items)
            Question(19, "I like to get revenge on authorities", "psychopathy"),
            Question(20, "I avoid dangerous situations", "psychopathy", is_reversed=True),
            Question(21, "Payback needs to be quick and nasty", "psychopathy"),
            Question(22, "People often say I'm out of control", "psychopathy"),
            Question(23, "It's true that I can be mean to others", "psychopathy"),
            Question(24, "People who mess with me always regret it", "psychopathy"),
            Question(25, "I have never gotten into trouble with the law", "psychopathy", is_reversed=True),
            Question(26, "I enjoy having sex with people I hardly know", "psychopathy"),
            Question(27, "I'll say anything to get what I want", "psychopathy"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """Calculate SD3 scores. Normalized to 0-100."""
        questions = self.get_questions()
        questions_by_number = {q.number: q for q in questions}
        
        factor_scores_raw = {
            "machiavellianism": [],
            "narcissism": [],
            "psychopathy": [],
        }
        
        for q_num, raw_score in responses.items():
            if q_num not in questions_by_number:
                continue
            question = questions_by_number[q_num]
            score = self.apply_reverse_scoring(raw_score, question.is_reversed)
            factor_scores_raw[question.factor].append(score)
        
        # Normalize to 0-100
        def normalize(scores: List[int]) -> float:
            if not scores:
                return 0.0
            mean = sum(scores) / len(scores)
            return ((mean - 1) / 4) * 100
        
        factor_scores = {
            factor: normalize(scores)
            for factor, scores in factor_scores_raw.items()
        }
        
        total_score = sum(factor_scores.values()) / len(factor_scores)
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores=factor_scores,
            questions_answered=len(responses),
            questions_total=self.get_question_count(),
        )
