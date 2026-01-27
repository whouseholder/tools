"""LLM integration with fallback strategy."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from loguru import logger

from ..utils.config import LLMConfig, LLMModelConfig


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, config: LLMModelConfig, api_key: str):
        """Initialize OpenAI provider."""
        from openai import OpenAI
        
        self.config = config
        self.client = OpenAI(api_key=api_key, timeout=config.timeout)
        logger.info(f"Initialized OpenAI provider with model: {config.model_name}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text from OpenAI."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )
            
            result = response.choices[0].message.content
            logger.debug(f"OpenAI generated response: {len(result)} chars")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""
    
    def __init__(self, config: LLMModelConfig, api_key: str):
        """Initialize Anthropic provider."""
        from anthropic import Anthropic
        
        self.config = config
        self.client = Anthropic(api_key=api_key, timeout=config.timeout)
        logger.info(f"Initialized Anthropic provider with model: {config.model_name}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text from Anthropic."""
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text
            logger.debug(f"Anthropic generated response: {len(result)} chars")
            return result
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise


class LLMManager:
    """Manager for LLM operations with fallback strategy."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM manager."""
        self.config = config
        
        # Initialize small model
        self.small_provider = self._create_provider(
            config.small_model,
            config.openai_api_key if config.small_model.provider == "openai" else config.anthropic_api_key
        )
        
        # Initialize large model
        self.large_provider = self._create_provider(
            config.large_model,
            config.openai_api_key if config.large_model.provider == "openai" else config.anthropic_api_key
        )
        
        logger.info("LLM Manager initialized with fallback strategy")
    
    def _create_provider(self, model_config: LLMModelConfig, api_key: str) -> LLMProvider:
        """Create LLM provider based on configuration."""
        if model_config.provider == "openai":
            return OpenAIProvider(model_config, api_key)
        elif model_config.provider == "anthropic":
            return AnthropicProvider(model_config, api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {model_config.provider}")
    
    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries_per_model: int = 2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text with fallback strategy.
        
        Tries small model first, then falls back to large model if needed.
        Returns dict with 'text', 'model_used', and 'attempts' info.
        """
        result = {
            'text': None,
            'model_used': None,
            'attempts': []
        }
        
        # Try small model first
        logger.info("Attempting generation with small model")
        for attempt in range(max_retries_per_model):
            try:
                text = self.small_provider.generate(prompt, system_prompt, **kwargs)
                result['text'] = text
                result['model_used'] = 'small'
                result['attempts'].append({
                    'model': 'small',
                    'attempt': attempt + 1,
                    'success': True
                })
                logger.info(f"Small model succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                logger.warning(f"Small model attempt {attempt + 1} failed: {e}")
                result['attempts'].append({
                    'model': 'small',
                    'attempt': attempt + 1,
                    'success': False,
                    'error': str(e)
                })
        
        # Fall back to large model
        logger.info("Falling back to large model")
        for attempt in range(max_retries_per_model):
            try:
                text = self.large_provider.generate(prompt, system_prompt, **kwargs)
                result['text'] = text
                result['model_used'] = 'large'
                result['attempts'].append({
                    'model': 'large',
                    'attempt': attempt + 1,
                    'success': True
                })
                logger.info(f"Large model succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                logger.warning(f"Large model attempt {attempt + 1} failed: {e}")
                result['attempts'].append({
                    'model': 'large',
                    'attempt': attempt + 1,
                    'success': False,
                    'error': str(e)
                })
        
        # All attempts failed
        logger.error("All LLM generation attempts failed")
        raise Exception("Failed to generate text after all retry attempts")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_large_model: bool = False,
        **kwargs
    ) -> str:
        """
        Generate text using specified model (no fallback).
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            use_large_model: If True, use large model directly
            **kwargs: Additional parameters for generation
        
        Returns:
            Generated text
        """
        provider = self.large_provider if use_large_model else self.small_provider
        model_type = "large" if use_large_model else "small"
        
        logger.info(f"Generating with {model_type} model")
        return provider.generate(prompt, system_prompt, **kwargs)
