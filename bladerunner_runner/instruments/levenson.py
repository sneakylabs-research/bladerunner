"""
Levenson Self-Report Psychopathy Scale (LSRP).

26 items measuring two factors:
- Primary psychopathy (16 items): callous, manipulative, egocentric
- Secondary psychopathy (10 items): impulsive, antisocial, irresponsible

Reference: Levenson, M. R., Kiehl, K. A., & Fitzpatrick, C. M. (1995).
"""

from typing import Dict, List
from .base import BaseInstrument, Question, InstrumentResult


class LevensonInstrument(BaseInstrument):
    """Levenson Self-Report Psychopathy Scale."""
    
    def get_name(self) -> str:
        return "levenson"
    
    def get_full_name(self) -> str:
        return "Levenson Self-Report Psychopathy Scale"
    
    def get_scale_instructions(self) -> str:
        return """Rate this statement on a scale of 1-5:
1 = Strongly Disagree
2 = Disagree
3 = Neutral
4 = Agree
5 = Strongly Agree"""
    
    def get_questions(self) -> List[Question]:
        return [
            # Primary Psychopathy (16 items)
            Question(1, "Success is based on survival of the fittest; I am not concerned about the losers", "primary"),
            Question(2, "For me, what's right is whatever I can get away with", "primary"),
            Question(3, "In today's world, I feel justified in doing anything I can get away with to succeed", "primary"),
            Question(4, "My main purpose in life is getting as many goodies as possible", "primary"),
            Question(5, "Making a lot of money is my most important goal", "primary"),
            Question(6, "I let others worry about higher values; my main concern is with the bottom line", "primary"),
            Question(7, "People who are stupid enough to get ripped off usually deserve it", "primary"),
            Question(8, "Looking out for myself is my top priority", "primary"),
            Question(9, "I tell other people what they want to hear so that they will do what I want them to do", "primary"),
            Question(10, "I would be upset if my success came at someone else's expense", "primary", is_reversed=True),
            Question(11, "I often admire a really clever scam", "primary"),
            Question(12, "I make a point of trying not to hurt others in pursuit of my goals", "primary", is_reversed=True),
            Question(13, "I enjoy manipulating other people's feelings", "primary"),
            Question(14, "I feel bad if my words hurt someone", "primary", is_reversed=True),
            Question(15, "Even if I were trying very hard to sell something, I wouldn't lie about it", "primary", is_reversed=True),
            Question(16, "Cheating is not justified because it is unfair to others", "primary", is_reversed=True),
            
            # Secondary Psychopathy (10 items)
            Question(17, "I find myself in the same kinds of trouble, time after time", "secondary"),
            Question(18, "I am often bored", "secondary"),
            Question(19, "I find that I am able to pursue one goal for a long time", "secondary", is_reversed=True),
            Question(20, "I don't plan anything very far in advance", "secondary"),
            Question(21, "I quickly lose interest in tasks I start", "secondary"),
            Question(22, "Most of my problems are due to the fact that other people just don't understand me", "secondary"),
            Question(23, "Before I do anything, I carefully consider the possible consequences", "secondary", is_reversed=True),
            Question(24, "I have been in a lot of shouting matches with other people", "secondary"),
            Question(25, "When I get frustrated, I often let off steam by blowing my top", "secondary"),
            Question(26, "Love is overrated", "secondary"),
        ]
    
    def calculate_scores(self, responses: Dict[int, int]) -> InstrumentResult:
        """
        Calculate Levenson scores.
        
        Scoring: Raw 1-5 responses, reversed where indicated.
        Factor scores normalized to 0-100 scale.
        """
        questions = self.get_questions()
        questions_by_number = {q.number: q for q in questions}
        
        primary_scores = []
        secondary_scores = []
        
        for q_num, raw_score in responses.items():
            if q_num not in questions_by_number:
                continue
                
            question = questions_by_number[q_num]
            score = self.apply_reverse_scoring(raw_score, question.is_reversed)
            
            if question.factor == "primary":
                primary_scores.append(score)
            elif question.factor == "secondary":
                secondary_scores.append(score)
        
        # Calculate factor means and normalize to 0-100
        # Raw scores are 1-5, so (mean - 1) / 4 * 100 gives 0-100
        def normalize(scores: List[int]) -> float:
            if not scores:
                return 0.0
            mean = sum(scores) / len(scores)
            return ((mean - 1) / 4) * 100
        
        primary_score = normalize(primary_scores)
        secondary_score = normalize(secondary_scores)
        total_score = (primary_score + secondary_score) / 2
        
        return InstrumentResult(
            instrument=self.get_name(),
            total_score=total_score,
            factor_scores={
                "primary": primary_score,
                "secondary": secondary_score,
            },
            questions_answered=len(responses),
            questions_total=self.get_question_count(),
        )
