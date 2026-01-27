"""Question validation module."""

from typing import Dict, List, Optional, Tuple
import re

from loguru import logger

from ..llm.llm_manager import LLMManager
from ..utils.config import ValidationConfig


class QuestionValidator:
    """Validates questions for relevance and answerability."""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        config: ValidationConfig
    ):
        """Initialize question validator."""
        self.llm_manager = llm_manager
        self.config = config
        logger.info("Question validator initialized")
    
    def validate(self, question: str) -> Dict[str, any]:
        """
        Validate a question.
        
        Returns dict with 'valid', 'reason', and individual check results.
        """
        results = {
            'valid': True,
            'reason': None,
            'checks': {}
        }
        
        # Length check
        length_valid, length_reason = self._check_length(question)
        results['checks']['length'] = {
            'valid': length_valid,
            'reason': length_reason
        }
        
        if not length_valid:
            results['valid'] = False
            results['reason'] = length_reason
            return results
        
        # Relevance check
        if self.config.check_relevance:
            relevance_valid, relevance_reason, relevance_score = self._check_relevance(question)
            results['checks']['relevance'] = {
                'valid': relevance_valid,
                'reason': relevance_reason,
                'score': relevance_score
            }
            
            if not relevance_valid:
                results['valid'] = False
                results['reason'] = relevance_reason
                return results
        
        # Answerability check
        if self.config.check_answerability:
            answerable_valid, answerable_reason = self._check_answerability(question)
            results['checks']['answerability'] = {
                'valid': answerable_valid,
                'reason': answerable_reason
            }
            
            if not answerable_valid:
                results['valid'] = False
                results['reason'] = answerable_reason
                return results
        
        logger.info(f"Question validation passed: {question[:50]}...")
        return results
    
    def _check_length(self, question: str) -> Tuple[bool, Optional[str]]:
        """Check question length."""
        length = len(question.strip())
        
        if length < self.config.min_question_length:
            return False, f"Question too short (minimum {self.config.min_question_length} characters)"
        
        if length > self.config.max_question_length:
            return False, f"Question too long (maximum {self.config.max_question_length} characters)"
        
        return True, None
    
    def _check_relevance(self, question: str) -> Tuple[bool, Optional[str], float]:
        """Check if question is relevant to data/SQL queries."""
        prompt = f"""Analyze if the following question is relevant to querying a database or analyzing data.

Question: {question}

Is this a question that can be answered with a SQL query against a database?

Respond with a JSON object in this exact format:
{{"relevant": true/false, "reason": "brief explanation", "confidence": 0.0-1.0}}"""
        
        try:
            response = self.llm_manager.generate(
                prompt=prompt,
                system_prompt="You are a question classifier. Respond ONLY with valid JSON.",
                use_large_model=False
            )
            
            # Parse response
            import json
            response_clean = response.strip()
            
            # Extract JSON if wrapped in markdown
            if '```json' in response_clean:
                response_clean = re.search(r'```json\s*(\{.+?\})\s*```', response_clean, re.DOTALL).group(1)
            elif '```' in response_clean:
                response_clean = re.search(r'```\s*(\{.+?\})\s*```', response_clean, re.DOTALL).group(1)
            
            result = json.loads(response_clean)
            
            is_relevant = result.get('relevant', False)
            reason = result.get('reason', 'Unknown')
            confidence = result.get('confidence', 0.0)
            
            if not is_relevant:
                return False, f"Question not relevant to data queries: {reason}", confidence
            
            return True, None, confidence
            
        except Exception as e:
            logger.warning(f"Relevance check failed: {e}, assuming relevant")
            return True, None, 1.0
    
    def _check_answerability(self, question: str) -> Tuple[bool, Optional[str]]:
        """Check if question is answerable."""
        prompt = f"""Analyze if the following question is specific and answerable with data.

Question: {question}

Is this question clear, specific, and answerable with database queries?

Respond with a JSON object in this exact format:
{{"answerable": true/false, "reason": "brief explanation"}}"""
        
        try:
            response = self.llm_manager.generate(
                prompt=prompt,
                system_prompt="You are a question analyzer. Respond ONLY with valid JSON.",
                use_large_model=False
            )
            
            # Parse response
            import json
            response_clean = response.strip()
            
            # Extract JSON if wrapped in markdown
            if '```json' in response_clean:
                response_clean = re.search(r'```json\s*(\{.+?\})\s*```', response_clean, re.DOTALL).group(1)
            elif '```' in response_clean:
                response_clean = re.search(r'```\s*(\{.+?\})\s*```', response_clean, re.DOTALL).group(1)
            
            result = json.loads(response_clean)
            
            is_answerable = result.get('answerable', True)
            reason = result.get('reason', 'Unknown')
            
            if not is_answerable:
                return False, f"Question not answerable: {reason}"
            
            return True, None
            
        except Exception as e:
            logger.warning(f"Answerability check failed: {e}, assuming answerable")
            return True, None
