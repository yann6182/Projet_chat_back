from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.model import User

def get_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Vérifie si l'utilisateur connecté est un administrateur.
    Lève une exception 403 si l'utilisateur n'est pas administrateur.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Vous devez être administrateur."
        )
    return current_user
