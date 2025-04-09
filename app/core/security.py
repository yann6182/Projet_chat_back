from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.model import User
from app.core.config import settings  # Utilisez les paramètres de configuration

# Contexte de hachage pour les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Instance OAuth2 pour l'extraction du token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

class TokenData(BaseModel):
    user_id: Optional[int] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username_or_email: str, password: str):
    # Recherche par username ou email
    user = db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Fonction pour détecter le token soit dans le header soit dans le cookie
async def get_token_from_header_or_cookie(
    token_header: str = Depends(oauth2_scheme),
    token_cookie: Optional[str] = Cookie(None, alias="access_token")
):
    return token_header or token_cookie

async def get_current_user(
    token: str = Depends(get_token_from_header_or_cookie),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Assurez-vous que user_id est bien un entier
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id_int)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Compte utilisateur inactif")
    return current_user

async def get_optional_user(
    token: str = Depends(get_token_from_header_or_cookie),
    db: Session = Depends(get_db)
):
    """
    Version optionnelle qui ne lève pas d'exception si l'utilisateur n'est pas connecté.
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if not user_id:
            return None
            
        # Convertir en entier
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return None
            
        user = db.query(User).filter(User.id == user_id_int).first()
        return user
    except:
        return None