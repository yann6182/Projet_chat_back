import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.model import User, PasswordReset
from app.core.config import settings
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

class PasswordResetService:
    def __init__(self):
        self.email_service = EmailService()

    def generate_reset_token(self, length=64):
        """Génère un token aléatoire pour la réinitialisation de mot de passe"""
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        return token

    def create_password_reset_request(self, db: Session, email: str):
        """
        Crée une demande de réinitialisation de mot de passe et envoie un email
        """
        # Vérifier si l'utilisateur existe
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Tentative de réinitialisation pour un email inexistant: {email}")
            # Pour des raisons de sécurité, ne pas indiquer que l'utilisateur n'existe pas
            return True

        # Générer un token unique
        token = self.generate_reset_token()
        
        # Créer une date d'expiration (24h par défaut)
        expires_at = datetime.utcnow() + timedelta(
            hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        )
        
        # Supprimer toutes les anciennes demandes de réinitialisation non utilisées
        db.query(PasswordReset).filter(
            PasswordReset.user_id == user.id,
            PasswordReset.is_used == False
        ).delete()
        db.commit()
        
        # Créer une nouvelle demande de réinitialisation
        password_reset = PasswordReset(
            user_id=user.id,
            reset_token=token,
            expires_at=expires_at,
            is_used=False
        )
        db.add(password_reset)
        db.commit()
        db.refresh(password_reset)
        
        # Envoyer l'email de réinitialisation
        sent = self.email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=token,
            username=user.username
        )
        
        if not sent:
            logger.error(f"Échec de l'envoi de l'email de réinitialisation pour {user.email}")
            # Indiquer l'échec tout en gardant l'entrée en base de données
            # pour permettre une nouvelle tentative d'envoi
            return False
            
        logger.info(f"Email de réinitialisation envoyé avec succès à {user.email}")
        return True

    def verify_reset_token(self, db: Session, token: str):
        """
        Vérifie si un token de réinitialisation est valide
        """
        # Rechercher le token dans la base de données
        reset_request = db.query(PasswordReset).filter(
            PasswordReset.reset_token == token,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_request:
            logger.warning(f"Tentative d'utilisation d'un token de réinitialisation invalide: {token[:10]}...")
            return None
            
        # Récupérer l'utilisateur associé
        user = db.query(User).filter(User.id == reset_request.user_id).first()
        if not user:
            logger.error(f"Token de réinitialisation valide mais utilisateur introuvable: {reset_request.user_id}")
            return None
            
        return user

    def reset_password(self, db: Session, token: str, new_password: str):
        """
        Réinitialise le mot de passe d'un utilisateur avec un token valide
        """
        # Vérifier si le token est valide
        user = self.verify_reset_token(db, token)
        if not user:
            return False
            
        # Import localisé pour éviter les importations circulaires
        from app.core.security import get_password_hash
        
        # Mettre à jour le mot de passe
        user.hashed_password = get_password_hash(new_password)
        
        # Marquer le token comme utilisé
        reset_request = db.query(PasswordReset).filter(
            PasswordReset.reset_token == token
        ).first()
        reset_request.is_used = True
        
        db.commit()
        logger.info(f"Mot de passe réinitialisé avec succès pour {user.email}")
        return True
