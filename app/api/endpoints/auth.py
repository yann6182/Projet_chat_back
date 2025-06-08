from datetime import timedelta
from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.security import (
    verify_password, 
    create_access_token, 
    get_password_hash, 
    get_current_user,
    get_optional_user
)
from app.core.config import settings
from app.db.database import get_db
from app.models.model import User
from fastapi.responses import JSONResponse
from app.schemas.schema import Token, UserCreate, UserSchema, PasswordResetRequest, PasswordResetVerify, PasswordResetConfirm
from app.services.password_reset_service import PasswordResetService

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_api")

router = APIRouter(prefix="/auth", tags=["auth"])
password_reset_service = PasswordResetService()

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning(f"Échec d'authentification: Utilisateur non trouvé - {email}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Échec d'authentification: Mot de passe incorrect pour {email}")
        return None
    logger.info(f"Authentification réussie pour l'utilisateur: {email} (ID: {user.id})")
    return user

@router.post("/login", response_model=None)
def login_for_access_token(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    logger.info(f"Tentative de connexion pour: {form_data.username}")
    logger.info(f"Headers de requête: {request.headers.get('user-agent')}")
    logger.info(f"Origin: {request.headers.get('origin')}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.error(f"Échec de connexion pour: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Créer le token avec 'sub' comme ID utilisateur
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # Utilisez l'ID comme 'sub' (convertir en string)
        expires_delta=access_token_expires
    )

    # Définir le cookie sécurisé
    cookie_params = {
        "key": "access_token",
        "value": access_token,
        "httponly": True,
        "max_age": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "expires": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "samesite": "none",
        "secure": True  # True en production avec HTTPS
    }
    
    logger.info(f"Configuration du cookie: {cookie_params}")
    response.set_cookie(**cookie_params)
    
    logger.info(f"Connexion réussie pour l'utilisateur: {user.username} (ID: {user.id})")
    
    # Retourner les informations de l'utilisateur connecté avec le token
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        },
        "status": "success",
        "message": "Connexion réussie"
    }

@router.post("/register", response_model=UserSchema)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Tentative d'inscription pour: {user_in.email}")
    
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        logger.warning(f"Échec d'inscription: Email déjà utilisé - {user_in.email}")
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    username_exists = db.query(User).filter(User.username == user_in.username).first()
    if username_exists:
        logger.warning(f"Échec d'inscription: Nom d'utilisateur déjà pris - {user_in.username}")
        raise HTTPException(
            status_code=400,
            detail="Ce nom d'utilisateur est déjà pris"
        )
    
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Inscription réussie pour: {user_in.email} (ID: {db_user.id})")
    return db_user

async def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
):
    """
    Dépendance pour récupérer l'utilisateur actuel à partir du cookie access_token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Non authentifié",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    logger.info(f"Vérification d'authentification - Path: {request.url.path}")
    logger.info(f"Cookies présents: {request.cookies}")
    
    if not access_token:
        logger.warning(f"Authentification échouée: Pas de cookie access_token")
        raise credentials_exception

    try:
        logger.info(f"Décodage du token JWT")
        payload = jwt.decode(
            access_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        logger.info(f"Token JWT décodé, user_id: {user_id}")
        
        if user_id is None:
            logger.warning(f"Authentification échouée: Aucun user_id dans le token")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        logger.warning(f"Authentification échouée: Utilisateur {user_id} non trouvé en base")
        raise credentials_exception
    
    logger.info(f"Utilisateur authentifié: {user.username} (ID: {user.id})")
    return user

async def get_optional_user(
    request: Request,
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
):
    """
    Version optionnelle de get_current_user qui ne lève pas d'exception
    si l'utilisateur n'est pas connecté.
    """
    logger.info(f"Vérification optionnelle d'authentification - Path: {request.url.path}")
    
    if not access_token:
        logger.info("Pas de cookie access_token trouvé")
        return None

    try:
        payload = jwt.decode(
            access_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.info("Aucun user_id dans le token")
            return None
            
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            logger.info(f"Utilisateur optionnel trouvé: {user.username} (ID: {user.id})")
        else:
            logger.info(f"Aucun utilisateur trouvé pour ID: {user_id}")
        return user
    except Exception as e:
        logger.error(f"Erreur lors de la vérification optionnelle: {str(e)}")
        return None

@router.post("/logout")
def logout(response: Response):
    logger.info("Déconnexion d'utilisateur")
    response = JSONResponse(content={"message": "Déconnecté avec succès"})
    # Supprimer le cookie en fixant une date d'expiration dans le passé
    response.delete_cookie(
        key="access_token",
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )
    logger.info("Cookie access_token supprimé")
    return response

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur actuellement connecté.
    """
    logger.info(f"Récupération des informations utilisateur pour: {current_user.username}")
    return current_user

@router.get("/check-auth")
async def check_auth(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Vérifie si l'utilisateur est authentifié sans lever d'exception.
    """
    logger.info(f"Vérification du statut d'authentification - Path: {request.url.path}")
    logger.info(f"Headers: {request.headers.get('user-agent')}")
    logger.info(f"Cookies présents: {request.cookies}")
    
    if current_user:
        logger.info(f"Utilisateur authentifié: {current_user.username} (ID: {current_user.id})")
        return {
            "authenticated": True, 
            "user_id": current_user.id, 
            "username": current_user.username,
            "email": current_user.email
        }
    
    logger.info("Aucun utilisateur authentifié")
    return {"authenticated": False}

@router.get("/check-admin")
async def check_admin_status(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Vérifie si l'utilisateur actuel a des privilèges d'administrateur.
    Retourne un statut 200 avec is_admin=True si c'est le cas, sinon is_admin=False.
    Ne renvoie pas d'erreur 401 si l'utilisateur n'est pas connecté.
    """
    if not current_user:
        logger.warning("Tentative de vérification du statut admin sans être connecté")
        return {
            "is_admin": False,
            "authenticated": False,
            "message": "Utilisateur non connecté"
        }
    
    logger.info(f"Vérification du statut admin pour l'utilisateur: {current_user.username} (ID: {current_user.id})")
    
    return {
        "is_admin": current_user.is_admin,
        "authenticated": True,
        "username": current_user.username,
        "email": current_user.email,
        "user_id": current_user.id
    }

@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Demande de réinitialisation de mot de passe par email
    """
    logger.info(f"Demande de réinitialisation de mot de passe pour: {request.email}")
    
    # Créer une demande de réinitialisation et envoyer un email
    success = password_reset_service.create_password_reset_request(db, request.email)
    
    # Pour des raisons de sécurité, toujours indiquer que la demande a réussi
    # même si l'email n'existe pas (pour éviter l'énumération des emails)
    return {
        "message": "Si votre email existe dans notre base, vous recevrez un email avec les instructions pour réinitialiser votre mot de passe."
    }

@router.post("/verify-reset-token")
async def verify_reset_token(
    request: PasswordResetVerify,
    db: Session = Depends(get_db)
):
    """
    Vérifie si un token de réinitialisation est valide
    """
    logger.info(f"Vérification d'un token de réinitialisation")
    
    user = password_reset_service.verify_reset_token(db, request.token)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Le token de réinitialisation est invalide ou a expiré"
        )
    
    return {
        "valid": True,
        "email": user.email,
        "username": user.username
    }

@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Réinitialise le mot de passe avec un token valide
    """
    logger.info(f"Réinitialisation de mot de passe avec token")
    
    success = password_reset_service.reset_password(db, request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Le token de réinitialisation est invalide ou a expiré"
        )
    
    return {
        "message": "Votre mot de passe a été réinitialisé avec succès"
    }