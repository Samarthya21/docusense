from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys & Provider configuration
    openai_api_key: str = Field(default="mock_key")
    gemini_api_key: str = Field(default="mock_key")
    llm_provider: str = Field(default="gemini")
    embedding_provider: str = Field(default="huggingface")
    
    # Model selections
    llm_model: str = Field(default="gpt-4o-mini")
    gemini_model: str = Field(default="gemini-3.6-flash")

    # Service configurations
    redis_url: str = Field(default="redis://localhost:6379/0")
    redpanda_bootstrap_servers: str = Field(default="localhost:9092")
    faiss_index_path: str = Field(default="./faiss_index")

    # Rate limiting & budgets
    rate_limit_per_ip: int = Field(default=10)
    rate_limit_window_seconds: int = Field(default=60)
    demo_budget_per_ip: int = Field(default=100)
    cache_ttl_seconds: int = Field(default=3600)

settings = Settings()
