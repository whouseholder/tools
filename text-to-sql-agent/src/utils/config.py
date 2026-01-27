"""Configuration management for the Text-to-SQL agent."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMModelConfig(BaseModel):
    """Configuration for an LLM model."""
    provider: str
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout: int = 30


class LLMConfig(BaseModel):
    """LLM configuration."""
    small_model: LLMModelConfig
    large_model: LLMModelConfig
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    provider: str = "chromadb"
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.85
    max_results: int = 5
    chromadb: Dict[str, Any] = {}
    pinecone: Dict[str, Any] = {}


class MetadataConfig(BaseModel):
    """Metadata store configuration."""
    hive: Dict[str, Any]
    index_refresh_interval: int = 3600
    cache_ttl: int = 1800


class QueryConfig(BaseModel):
    """Query generation and validation configuration."""
    dialect: str = "hive"
    syntax_check_enabled: bool = True
    max_retries_per_model: int = 2
    max_execution_time: int = 300
    max_result_rows: int = 10000


class ValidationConfig(BaseModel):
    """Validation configuration."""
    min_question_length: int = 5
    max_question_length: int = 500
    check_relevance: bool = True
    check_answerability: bool = True
    check_similar_questions: bool = True
    prompt_on_similar: bool = True


class FeedbackConfig(BaseModel):
    """Feedback system configuration."""
    enabled: bool = True
    storage_path: str = "./data/feedback/feedback.db"
    eval_mode: bool = False
    auto_store_threshold: float = 0.9
    allow_user_feedback: bool = True


class MemoryConfig(BaseModel):
    """Memory management configuration."""
    max_context_messages: int = 10
    max_context_tokens: int = 4000
    cache_enabled: bool = True
    cache_path: str = "./data/cache"
    cache_ttl: int = 3600


class VisualizationConfig(BaseModel):
    """Visualization configuration."""
    default_format: str = "table"
    auto_suggest_charts: bool = True
    supported_chart_types: List[str] = []


class APIConfig(BaseModel):
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = []


class TeamsConfig(BaseModel):
    """Microsoft Teams integration configuration."""
    enabled: bool = False
    app_id: Optional[str] = None
    app_password: Optional[str] = None
    endpoint: str = "/api/teams/messages"


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = "Text-to-SQL Agent"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"


class Config(BaseModel):
    """Main configuration class."""
    app: AppConfig
    llm: LLMConfig
    vector_store: VectorStoreConfig
    metadata: MetadataConfig
    query: QueryConfig
    validation: ValidationConfig
    feedback: FeedbackConfig
    memory: MemoryConfig
    visualization: VisualizationConfig
    api: APIConfig
    teams: TeamsConfig


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file with environment variable substitution."""
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    
    config_file = Path(config_path)
    
    # Fall back to example config if main config doesn't exist
    if not config_file.exists():
        config_file = Path("config/config.example.yaml")
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Substitute environment variables
    config_data = _substitute_env_vars(config_data)
    
    return Config(**config_data)


def _substitute_env_vars(data: Any) -> Any:
    """Recursively substitute environment variables in configuration."""
    if isinstance(data, dict):
        return {k: _substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        env_var = data[2:-1]
        return os.getenv(env_var, "")
    return data


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
