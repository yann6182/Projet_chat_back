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
    DATABASE_URL: str = "postgresql://postgres:Messi6@localhost:5432/chatbotdb"
    #DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # Variables pour JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "votre_clé_secrète_par_défaut")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()

