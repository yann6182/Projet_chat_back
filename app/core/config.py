import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Juridica API"
    DESCRIPTION: str = "API pour le projet Juridica"
    VERSION: str = "0.1.0"
    load_dotenv()
    # Variables d'environnement pour la base de données
    DATABASE_URL: str = "postgresql://postgres:Ronaldo10%40@localhost:5432/chatbotdb"
    #DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # Clé API Mistral pour les embeddings
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")  # Laisser vide par défaut
    
    # Variables pour JWT
    SECRET_KEY: str = (
        "2Z2UKaxPogMx0Ct0EOzCIK5YdDTh0qmsnkxhxsptnIA"  # À mettre en variable d'environnement
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours
    COOKIE_SECURE: bool = True  # Mettre True en production avec HTTPS
    class Config:
        env_file = ".env"

settings = Settings()

