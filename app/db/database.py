from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ajouter les paramètres d'encodage à l'URL
if "postgresql" in settings.DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = f"{settings.DATABASE_URL}?client_encoding=utf8"
else:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

# Configurer l'encodage de la session
def configure_encoding():
    with engine.connect() as connection:
        connection.execute(text("SET client_encoding TO 'UTF8';"))
        connection.execute(text("SET standard_conforming_strings TO 'on';"))
        connection.commit()

# Appeler la configuration de l'encodage
configure_encoding()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
