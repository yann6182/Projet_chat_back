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
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    # Clé API Mistral pour les embeddings
    MISTRAL_API_KEY: str = os.getenv(
        "MISTRAL_API_KEY", "")  # Laisser vide par défaut

    JWT_KEY: str
    # Variables pour JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY",
                                ""  # À mettre en variable d'environnement
                                )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours
    COOKIE_SECURE: bool = True  # Mettre True en production avec HTTPS

    # Configuration pour les emails
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", ""))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    APP_NAME: str = os.getenv("APP_NAME", "Juridica")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    class Config:
        env_file = ".env"


settings = Settings()
