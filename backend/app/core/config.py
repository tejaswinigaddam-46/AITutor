from typing import List, Union, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AITutor-RAG"
    BACKEND_PORT: int = 8000
    
    # Security
    API_KEY_NAME: str = "X-API-KEY"
    # No default value for API_KEY to force it to be set in environment/dotenv
    API_KEY: str 
    DISABLE_API_KEY_AUTH: bool = False

    # JWT Configuration
    JWT_SECRET: str = ""
    JWT_ISSUER: str = "sms-backend"
    JWT_AUDIENCE: str = "sms-client"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: Any = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return []

    # API Keys - Required for production
    EMBEDDING_API_KEY: str 
    GROQ_API_KEY: str = "" # Default empty if not provided
    XAI_API_KEY: str = "" # Added for Grok integration
    
    # Models
    EMBEDDING_MODEL: str = ""
    LLM_MODEL: str = ""

    # DB
    VECTOR_DB_TYPE: str = "postgres"
    VECTOR_DB_PATH: str = ""
    
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    # No default value for DB_PASSWORD to force security in production
    DB_PASSWORD: str 
    
    DB_MIN_CONNECTIONS: int = 1
    DB_MAX_CONNECTIONS: int = 10

    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file=".env",
        extra="ignore" # Ignore extra env vars not defined in the class
    )

settings = Settings()
