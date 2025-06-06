import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Juridica API"
    DESCRIPTION: str = "API pour le projet Juridica"
    VERSION: str = "0.1.0"
    load_dotenv()
    # Variable pour la base de données
    DATABASE_URL: str = "postgresql://postgres:bababar@localhost:5432/juridicadb"
    
    # Variable pour Clé API Mistral
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    
    # Variable pour JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours
    COOKIE_SECURE: bool = True  # Mettre True en production avec HTTPS
    class Config:
        env_file = ".env"

settings = Settings()

