import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.app_name = settings.APP_NAME
        self.app_url = settings.APP_URL

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """
        Envoie un email en HTML et texte brut
        """
        try:
            # Créer le message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.app_name} <{self.from_email}>"
            message["To"] = to_email

            # Créer les parties du message (texte et HTML)
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # Établir une connexion sécurisée avec le serveur SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Sécuriser la connexion
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())

            logger.info(f"Email envoyé avec succès à {to_email}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {str(e)}")
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str, username: str):
        """
        Envoie un email de réinitialisation de mot de passe
        """
        # Construire le lien de réinitialisation
        reset_url = f"{self.app_url}/reset-password?token={reset_token}"
        
        # Contenu HTML de l'email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4a86e8; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; border: 1px solid #ddd; }}
                .button {{ display: inline-block; background-color: #4a86e8; color: white; padding: 10px 20px; 
                           text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 0.8em; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{self.app_name}</h2>
                </div>
                <div class="content">
                    <p>Bonjour {username},</p>
                    <p>Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte.</p>
                    <p>Pour réinitialiser votre mot de passe, cliquez sur le lien ci-dessous :</p>
                    <a href="{reset_url}" class="button">Réinitialiser mon mot de passe</a>
                    <p>Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email.</p>
                    <p>Ce lien expirera dans 24 heures.</p>
                </div>
                <div class="footer">
                    <p>&copy; {self.app_name}. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Version texte de l'email
        text_content = f"""
        Bonjour {username},
        
        Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte.
        
        Pour réinitialiser votre mot de passe, cliquez sur le lien ci-dessous :
        {reset_url}
        
        Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email.
        
        Ce lien expirera dans 24 heures.
        
        Cordialement,
        L'équipe {self.app_name}
        """
        
        subject = f"{self.app_name} - Réinitialisation de mot de passe"
        return self.send_email(to_email, subject, html_content, text_content)
