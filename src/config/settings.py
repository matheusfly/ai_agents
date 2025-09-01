from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Model settings
    QWEN_MODEL: str = "qwen3:latest"
    GEMMA_MODEL: str = "gemma3:latest"
    
    # LangSmith settings
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "multi-agent-prompt-engine"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Workflow settings
    MAX_ITERATIONS: int = 30
    VERBOSE_LOGGING: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()