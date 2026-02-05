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
    
    def validate(self, question: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, any]:
        """
        Validate a question with optional conversation context.
        
        Args:
            question: The question to validate
            conversation_history: Optional list of previous messages with 'role', 'content', and optional 'metadata'
        
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
        
        # Context-aware relevance check (uses conversation history if available)
        if self.config.check_relevance:
            relevance_valid, relevance_reason, relevance_score = self._check_relevance_with_context(
                question, 
                conversation_history
            )
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
    
    def _check_relevance_with_context(
        self, 
        question: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> Tuple[bool, Optional[str], float]:
        """Check if question is relevant to data/SQL queries, considering conversation context."""
        
        # Build context summary from conversation history
        context_summary = ""
        if conversation_history:
            # Get last few messages for context
            recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:200]  # Truncate long messages
                metadata = msg.get('metadata', {})
                
                if role == 'user':
                    context_summary += f"\nPrevious user question: {content}"
                elif role == 'assistant' and metadata.get('sql_query'):
                    context_summary += f"\nExecuted SQL: {metadata['sql_query'][:100]}"
        
        # Build prompt with context awareness
        if context_summary:
            prompt = f"""Analyze if the following question is relevant given the conversation context.

CONVERSATION CONTEXT:{context_summary}

CURRENT QUESTION: {question}

Is this question:
1. About data, analytics, or visualizations?
2. A reasonable follow-up to the previous conversation?

VALIDATION RULES:
✅ ANSWER "relevant: true" FOR:
- ANY standalone data question (customers, revenue, users, transactions, etc.)
- Visualization requests related to previous data (show as chart, plot this, make it a pie chart)
- Analytics questions that build on previous queries (show trends, compare with, break down by)
- Follow-ups that reference previous results (these customers, those users, that data, it, them)
- Questions about the same entities discussed in conversation

❌ ANSWER "relevant: false" FOR:
- Follow-ups about COMPLETELY DIFFERENT topics (e.g., previous Q about customers, current Q about pizza preferences)
- Questions about non-database topics (weather, sports, news, general knowledge)
- Pure chitchat or greetings
- Nonsensical input

IMPORTANT: If the question references "these", "those", "that", "them", "it" - check if it's related to the conversation context.
Example: Previous Q: "top customers", Current Q: "what pizza do they like?" → FALSE (unrelated)
Example: Previous Q: "top customers", Current Q: "what is their churn risk?" → TRUE (related)

Respond with a JSON object:
{{"relevant": true/false, "reason": "brief explanation", "confidence": 0.0-1.0}}"""
        else:
            # No context - use simple relevance check
            prompt = f"""Analyze if the following question is about data that could be in a database.

Question: {question}

Is this question asking about data, analytics, or visualizations?

ANSWER "relevant: true" FOR:
- ANY question about data (customers, revenue, users, transactions, metrics, KPIs, etc.)
- ANY visualization request (charts, graphs, plots, show data, display data)
- ANY analytics question (trends, patterns, comparisons, rankings)
- ANY data formatting request (as table, as chart, sorted by, grouped by)

ONLY ANSWER "relevant: false" FOR:
- Questions about completely unrelated topics (weather, sports scores, news, celebrities)
- Questions that CANNOT involve database data at all
- Pure conversational questions (greetings, chitchat)
- Nonsensical or gibberish input

BE LENIENT - when in doubt, answer true.

Respond with a JSON object:
{{"relevant": true, "reason": "data/analytics question", "confidence": 0.95}}"""
        
        try:
            response = self.llm_manager.generate(
                prompt=prompt,
                system_prompt="You are a context-aware question validator. Analyze if questions are relevant to database queries, considering conversation history. Respond ONLY with valid JSON.",
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
    
    def _check_relevance(self, question: str) -> Tuple[bool, Optional[str], float]:
        """Check if question is relevant (backward compatibility - no context)."""
        return self._check_relevance_with_context(question, None)
    
    def _check_answerability(self, question: str) -> Tuple[bool, Optional[str]]:
        """Check if question is answerable."""
        prompt = f"""Analyze if the following question could be answered with database data.

Question: {question}

Can this question be answered by querying or visualizing database data?

ANSWER "answerable: true" FOR:
- Questions about specific metrics (churn, revenue, count, average, etc.)
- Questions with references like "these", "that", "it" (likely follow-ups)
- Visualization requests for existing data
- Questions that mention data entities (customers, users, transactions, etc.)
- Questions that could be answered if we knew the database schema

ONLY ANSWER "answerable: false" FOR:
- Questions requiring external data not in any database (weather, stock prices)
- Questions requiring prediction of future events
- Questions requiring subjective opinions
- Completely nonsensical questions

BE LENIENT - if it could possibly be answered with database data, answer true.

Respond with a JSON object in this exact format:
{{"answerable": true, "reason": "data question"}}"""
        
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
