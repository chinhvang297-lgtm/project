"""
Application configuration using Pydantic BaseSettings.

Supports loading from environment variables and .env file.
Centralizes all configuration in one place for easy management.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from langchain_openai import ChatOpenAI

from app.core.logger import setup_logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    dashscope_api_key: str = Field(..., alias="DASHSCOPE_API_KEY")
    llm_model: str = Field(default="qwen3-max", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="LLM_BASE_URL",
    )

    # Agent Configuration
    agent_timeout: int = Field(default=60, alias="AGENT_TIMEOUT")
    agent_max_retries: int = Field(default=2, alias="AGENT_MAX_RETRIES")

    # Search Configuration
    tavily_api_key: str = Field(..., alias="TAVILY_API_KEY")
    tavily_max_results: int = Field(default=5, alias="TAVILY_MAX_RESULTS")

    # RAG Configuration
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    rag_rerank_top_n: int = Field(default=3, alias="RAG_RERANK_TOP_N")

    # Cache Configuration
    cache_ttl_prediction: int = Field(default=600, alias="CACHE_TTL_PREDICTION")
    cache_ttl_search: int = Field(default=300, alias="CACHE_TTL_SEARCH")

    # Database
    database_url: str = Field(
        default="sqlite:///./nba_prediction.db", alias="DATABASE_URL"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }


# Initialize settings
settings = Settings()

# Export API keys to os.environ so third-party SDKs can find them
os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)
os.environ.setdefault("DASHSCOPE_API_KEY", settings.dashscope_api_key)

# Setup structured logging
setup_logging(level=settings.log_level)

# Initialize LLM
llm = ChatOpenAI(
    api_key=settings.dashscope_api_key,
    base_url=settings.llm_base_url,
    model=settings.llm_model,
    temperature=settings.llm_temperature,
)
