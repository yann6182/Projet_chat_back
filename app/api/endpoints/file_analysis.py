from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, Body
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.document_service import DocumentService
from app.services.chat_service import ChatService
from app.schemas.document import DocumentUploadResponse, DocumentAnalysisRequest, DocumentAnalysisResponse
from app.schemas.chat import ChatRequest, ChatResponse, DocumentContext
from app.models.model import User
from app.api.deps import get_current_user
import os
import shutil
import uuid
import logging

router = APIRouter(prefix="/file-analysis", tags=["file-analysis"])

# Initialiser les services
document_service = DocumentService()
chat_service = ChatService()

logger = logging.getLogger(__name__)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Télécharge un document pour analyse et traitement.
    """
    try:
        document_id = await document_service.save_document(file.file, file.filename)
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="uploaded"
        )
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du fichier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_file(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyse un document téléchargé pour vérifier son orthographe, sa grammaire et sa conformité légale.
    """
    try:
        analysis_result = await document_service.analyze_document(request.document_id)
        return analysis_result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=ChatResponse)
async def query_document(
    request: ChatRequest,
    document_id: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pose une question sur un document spécifique.
    """
    try:
        # Récupérer le contenu du document
        file_path, filename = document_service.find_document_by_id(document_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Document avec l'ID {document_id} non trouvé")
            
        # Extraire le texte du document
        document_text = document_service.extract_text(file_path)
        
        # Créer un contexte de document pour le chat service
        context_document = DocumentContext(
            content=document_text,
            source=filename,
            page=None
        )
        
        # Ajouter le document au contexte de la requête
        if not hasattr(request, 'context_documents'):
            request.context_documents = []
        request.context_documents.append(context_document)
        
        # Générer une nouvelle conversation si aucune n'est spécifiée
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # Traiter la requête avec le service de chat
        response = await chat_service.process_query(
            request=request,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/correct")
async def correct_document(
    document_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Analyse et corrige un document pour améliorer son orthographe, sa grammaire et sa conformité légale.
    """
    try:
        # Analyser d'abord le document
        analysis_result = await document_service.analyze_document(document_id)
        
        # Simuler la correction automatique
        # Note: Ce code devrait être remplacé par une véritable implémentation de correction
        corrected_id = f"{document_id}_corrected"
        file_path, filename = document_service.find_document_by_id(document_id)
        _, ext = os.path.splitext(filename)
        
        # Dans une implémentation réelle, on utiliserait la méthode auto_correct_document
        # Pour l'instant, on crée juste une copie du fichier original
        if file_path:
            corrected_filename = f"{corrected_id}{ext}"
            corrected_path = os.path.join(document_service.upload_dir, corrected_filename)
            shutil.copy2(file_path, corrected_path)
            
            return {
                "original_document_id": document_id,
                "corrected_document_id": corrected_id,
                "filename": corrected_filename,
                "corrections_applied": len(analysis_result.spelling_errors) + len(analysis_result.grammar_errors),
                "status": "corrected"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Document avec l'ID {document_id} non trouvé")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la correction du document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_document(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Télécharge un document analysé ou corrigé.
    """
    try:
        file_path = os.path.join(document_service.upload_dir, filename)
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path, 
                filename=filename,
                media_type="application/octet-stream"
            )
        else:
            raise HTTPException(status_code=404, detail=f"Fichier {filename} non trouvé")
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du fichier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
