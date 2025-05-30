from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import logging

from app.core.admin import get_admin_user
from app.db.database import get_db
from app.models.model import User
from app.schemas.document import DocumentResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Répertoire où les documents sources seront stockés
SOURCES_DIR = os.path.join("data", "legal_docs")

# S'assurer que le répertoire existe
os.makedirs(SOURCES_DIR, exist_ok=True)

@router.post("/upload-source", response_model=DocumentResponse)
async def upload_source_document(
    file: UploadFile = File(...),
    description: str = Form(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Télécharge un document source (PDF, TXT, DOCX, etc.) et le stocke dans le répertoire des sources.
    Seuls les administrateurs peuvent utiliser cet endpoint.
    """
    # Vérifier si le fichier a une extension valide
    valid_extensions = [".pdf", ".txt", ".docx", ".doc"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format de fichier non pris en charge. Extensions acceptées: {', '.join(valid_extensions)}"
        )
    
    # Créer le chemin où le fichier sera enregistré
    file_path = os.path.join(SOURCES_DIR, file.filename)
    
    # Vérifier si le fichier existe déjà
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un fichier avec ce nom existe déjà: {file.filename}"
        )
    
    try:
        # Enregistrer le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Document source ajouté: {file.filename}")
        
        return {
            "filename": file.filename,
            "filepath": file_path,
            "size": os.path.getsize(file_path),
            "description": description or "Document source pour RAG"
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du document source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du traitement du fichier"
        )

@router.get("/list-sources", response_model=List[DocumentResponse])
async def list_source_documents(
    admin_user: User = Depends(get_admin_user)
):
    """
    Liste tous les documents sources disponibles.
    Seuls les administrateurs peuvent utiliser cet endpoint.
    """
    try:
        documents = []
        
        # Parcourir le répertoire des sources
        for filename in os.listdir(SOURCES_DIR):
            file_path = os.path.join(SOURCES_DIR, filename)
            
            # Ne prendre que les fichiers (pas les dossiers)
            if os.path.isfile(file_path):
                documents.append({
                    "filename": filename,
                    "filepath": file_path,
                    "size": os.path.getsize(file_path),
                    "description": "Document source pour RAG"
                })
        
        return documents
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des documents"
        )

@router.delete("/delete-source/{filename}")
async def delete_source_document(
    filename: str,
    admin_user: User = Depends(get_admin_user)
):
    """
    Supprime un document source.
    Seuls les administrateurs peuvent utiliser cet endpoint.
    """
    file_path = os.path.join(SOURCES_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document non trouvé: {filename}"
        )
    
    try:
        os.remove(file_path)
        return {"message": f"Document supprimé avec succès: {filename}"}
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la suppression du document"
        )

@router.post("/reindex-sources")
async def reindex_source_documents(
    admin_user: User = Depends(get_admin_user)
):
    """
    Déclenche la réindexation des documents sources pour le système RAG.
    Seuls les administrateurs peuvent utiliser cet endpoint.
    """
    try:
        # Importer le script de réindexation
        import subprocess
        import sys
        
        # Exécuter le script de réindexation
        process = subprocess.run(
            [sys.executable, "scripts/reindex.py", "--data", SOURCES_DIR],
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"Erreur lors de la réindexation: {process.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la réindexation des documents"
            )
        
        return {
            "message": "Documents réindexés avec succès",
            "details": process.stdout
        }
    except Exception as e:
        logger.error(f"Erreur lors de la réindexation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la réindexation des documents"
        )
