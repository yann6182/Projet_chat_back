"""
Service pour gérer les fichiers uploadés par l'utilisateur.
Permet d'extraire le texte des fichiers pour l'utiliser dans le RAG.
"""
from typing import Dict, List, Optional, BinaryIO
import os
import logging
from pathlib import Path
import tempfile
import uuid
import PyPDF2
import docx
from fastapi import UploadFile

# Configuration du logger
logger = logging.getLogger(__name__)

class FileService:
    """Service pour traiter les fichiers uploadés et en extraire le contenu."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialise le service de fichiers.
        
        Args:
            temp_dir: Répertoire temporaire pour stocker les fichiers pendant leur traitement.
                     Si None, utilise le répertoire temporaire du système.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"Service de fichiers initialisé avec le répertoire temporaire: {self.temp_dir}")
    
    async def extract_text_from_upload(self, file: UploadFile) -> Dict:
        """
        Extrait le texte d'un fichier uploadé.
        
        Args:
            file: Le fichier uploadé via FastAPI
            
        Returns:
            Un dictionnaire contenant le contenu extrait et les métadonnées
            {
                'content': str,     # Contenu textuel extrait
                'source': str,      # Nom du fichier
                'mime_type': str,   # Type MIME
                'size': int,        # Taille en octets
            }
        """
        temp_file_path = None
        try:
            # Créer un nom de fichier temporaire unique
            temp_file_path = Path(self.temp_dir) / f"{uuid.uuid4()}_{file.filename}"
            
            # Lire le contenu du fichier uploadé
            contents = await file.read()
            
            # Écrire dans un fichier temporaire
            with open(temp_file_path, 'wb') as f:
                f.write(contents)
            
            # Déterminer l'extracteur en fonction de l'extension
            file_extension = Path(file.filename).suffix.lower()
            mime_type = file.content_type
            
            content = ""
            if file_extension == '.pdf':
                content = self._extract_text_from_pdf(temp_file_path)
            elif file_extension == '.docx':
                content = self._extract_text_from_docx(temp_file_path)
            elif file_extension in ['.txt', '.py', '.js', '.html', '.css', '.md']:
                content = self._extract_text_from_text_file(temp_file_path)
            else:
                logger.warning(f"Type de fichier non supporté: {file_extension}")
                content = f"Le format de fichier {file_extension} n'est pas pris en charge pour l'extraction de texte."
            
            return {
                'content': content,
                'source': file.filename,
                'mime_type': mime_type,
                'size': len(contents)
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de texte du fichier {file.filename}: {str(e)}")
            return {
                'content': f"Impossible d'extraire le texte: {str(e)}",
                'source': file.filename,
                'mime_type': file.content_type,
                'size': 0
            }
        finally:
            # Nettoyer le fichier temporaire
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            # Remettre le curseur au début du fichier pour une utilisation ultérieure
            await file.seek(0)
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extrait le texte d'un fichier PDF."""
        text = ""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
            return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de texte du PDF: {str(e)}")
            return f"Erreur lors de l'extraction du texte du PDF: {str(e)}"
    
    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extrait le texte d'un fichier DOCX."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de texte du DOCX: {str(e)}")
            return f"Erreur lors de l'extraction du texte du DOCX: {str(e)}"
    
    def _extract_text_from_text_file(self, file_path: Path) -> str:
        """Extrait le texte d'un fichier texte."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Essayer avec une autre encodage si UTF-8 échoue
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier texte: {str(e)}")
                return f"Erreur lors de la lecture du fichier texte: {str(e)}"
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier texte: {str(e)}")
            return f"Erreur lors de la lecture du fichier texte: {str(e)}"
