# app/db/session_manager.py
from contextlib import contextmanager
from typing import Generator
import logging
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

@contextmanager
def db_session() -> Generator:
    """
    Context manager pour les sessions de base de données.
    Assure la fermeture correcte de la session, même en cas d'exception.
    
    Yields:
        Un objet session SQLAlchemy.
    
    Usage:
        with db_session() as session:
            # Utiliser la session
            result = session.query(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()
