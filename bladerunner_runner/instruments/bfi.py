"""
Big Five Inventory (BFI-44).

44 items measuring five factors:
- Extraversion (8 items)
- Agreeableness (9 items)
- Conscientiousness (9 items)
- Neuroticism (8 items)
- Openness (10 items)

Reference: John, O. P., & Srivastava, S. (1999).
"""

from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class BFIInstrument(BaseInstrument):
    """Big Five Inventory (BFI-44)."""
    
    def get_name(self) -> str:
        return "bfi"
    
    def get_full_name(self) -> str:
        return "Big Five Inventory (BFI-44)"
    
    def get_scale_instructions(self) -> str:
        return """Rate how well this describes you on a scale of 1-5:
1 = Disagree strongly
2 = Disagree a little
3 = Neither agree nor disagree
4 = Agree a little
5 = Agree strongly

"I see myself as someone who...\""""
    
    def get_questions(self) -> List[Question]:
        return [
            # Extraversion (8 items)
            Question(1, "Is talkative", "extraversion"),
            Question(6, "Is reserved", "extraversion", is_reversed=True),
            Question(11, "Is full of energy", "extraversion"),
            Question(16, "Generates a lot of enthusiasm", "extraversion"),
            Question(21, "Tends to be quiet", "extraversion", is_reversed=True),
            Question(26, "Has an assertive personality", "extraversion"),
            Question(31, "Is sometimes shy, inhibited", "extraversion", is_reversed=True),
            Question(36, "Is outgoing, sociable", "extraversion"),
            
            # Agreeableness (9 items)
            Question(2, "Tends to find fault with others", "agreeableness", is_reversed=True),
            Question(7, "Is helpful and unselfish with others", "agreeableness"),
            Question(12, "Starts quarrels with others", "agreeableness", is_reversed=True),
            Question(17, "Has a forgiving nature", "agreeableness"),
            Question(22, "Is generally trusting", "agreeableness"),
            Question(27, "Can be cold and aloof", "agreeableness", is_reversed=True),
            Question(32, "Is considerate and kind to almost everyone", "agreeableness"),
            Question(37, "Is sometimes rude to others", "agreeableness", is_reversed=True),
            Question(42, "Likes to cooperate with others", "agreeableness"),
            
            # Conscientiousness (9 items)
            Question(3, "Does a thorough job", "conscientiousness"),
            Question(8, "Can be somewhat careless", "conscientiousness", is_reversed=True),
            Question(13, "Is a reliable worker", "conscientiousness"),
            Question(18, "Tends to be disorganized", "conscientiousness", is_reversed=True),
            Question(23, "Tends to be lazy", "conscientiousness", is_reversed=True),
            Question(28, "Perseveres until the task is finished", "conscientiousness"),
            Question(33, "Does things efficiently", "conscientiousness"),
            Question(38, "Makes plans and follows through with them", "conscientiousness"),
            Question(43, "Is easily distracted", "conscientiousness", is_reversed=True),
            
            # Neuroticism (8 items)
            Question(4, "Is depressed, blue", "neuroticism"),
            Question(9, "Is relaxed, handles stress well", "neuroticism", is_reversed=True),
            Question(14, "Can be tense", "neuroticism"),
            Question(19, "Worries a lot", "neuroticism"),
            Question(24, "Is emotionally stable, not easily upset", "neuroticism", is_reversed=True),
            Question(29, "Can be moody", "neuroticism"),
            Question(34, "Remains calm in tense situations", "neuroticism", is_reversed=True),
            Question(39, "Gets nervous easily", "neuroticism"),
            
            # Openness (10 items)
            Question(5, "Is original, comes up with new ideas", "openness"),
            Question(10, "Is curious about many different things", "openness"),
            Question(15, "Is ingenious, a deep thinker", "openness"),
            Question(20, "Has an active imagination", "openness"),
            Question(25, "Is inventive", "openness"),
            Question(30, "Values artistic, aesthetic experiences", "openness"),
            Question(35, "Prefers work that is routine", "openness", is_reversed=True),
            Question(40, "Likes to reflect, play with ideas", "openness"),
            Question(41, "Has few artistic interests", "openness", is_reversed=True),
            Question(44, "Is sophisticated in art, music, or literature", "openness"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate BFI scores.
        
        Scoring: Raw 1-5 responses, reversed where indicated.
        Factor scores normalized to 0-100 scale.
        """
        questions = self.get_questions()
        questions_by_number = {q.number: q for q in questions}
        
        factor_scores_raw: Dict[str, List[int]] = {
            "extraversion": [],
            "agreeableness": [],
            "conscientiousness": [],
            "neuroticism": [],
            "openness": [],
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
        
        # Total is average of factors
        total_score = sum(factor_scores.values()) / len(factor_scores)
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores=factor_scores,
            questions_answered=len(responses),
            questions_total=self.get_question_count(),
        )
