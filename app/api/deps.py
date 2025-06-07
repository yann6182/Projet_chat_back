# app/api/deps.py
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.model import User
from app.core.security import get_current_user as security_get_current_user, get_current_active_user as security_get_current_active_user

# Re-export the functions for consistency
async def get_current_user(
    current_user: User = Depends(security_get_current_user)
) -> User:
    return current_user

async def get_current_active_user(
    current_user: User = Depends(security_get_current_active_user)
) -> User:
    return current_user
