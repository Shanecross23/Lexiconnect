from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lexiconnect"

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js development
        "http://frontend:3000",  # Docker internal network
        "https://your-app.vercel.app",  # Vercel production
        "https://your-custom-domain.com",  # Custom domain
    ]

    # Neo4j Database
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Google Cloud Platform (optional - can run without)
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_SERVICE_ACCOUNT_FILE: str = os.getenv("GCP_SERVICE_ACCOUNT_FILE", "")
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
    USE_GCP: bool = bool(GCP_PROJECT_ID and GCP_SERVICE_ACCOUNT_FILE)

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
