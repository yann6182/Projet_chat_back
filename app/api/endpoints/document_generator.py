from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
import os
import logging
import json

from app.db.database import get_db
from app.services.document_generator_service import DocumentGeneratorService
from app.models.model import User, Conversation, Question, Response
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/document-generator", tags=["document-generator"])
document_generator = DocumentGeneratorService()

# Modèles de données pour les requêtes API
class GenerateDocumentRequest(BaseModel):
    conversation_id: Optional[str] = None
    question_id: Optional[int] = None
    format: str  # "pdf" ou "docx"
    title: Optional[str] = None
    include_question_history: bool = False
    include_sources: bool = True

class DocumentResponse(BaseModel):
    filename: str
    url: str

@router.post("/generate", response_model=DocumentResponse)
async def generate_document(
    request: GenerateDocumentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Génère un document (PDF ou Word) à partir d'une réponse spécifique
    ou d'une conversation complète.
    """
    try:
        # Vérifier si la conversation existe et appartient à l'utilisateur
        conversation = None
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.uuid == request.conversation_id,
                Conversation.user_id == current_user.id
            ).first()
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation non trouvée ou non autorisée")
        
        # Contenu à inclure dans le document
        title = request.title or "Document généré par Juridica"
        content = ""
        sources = []
        metadata = {
            "Utilisateur": current_user.username,
            "Date": conversation.created_at.strftime("%d/%m/%Y") if conversation else None,
            "Type": "Réponse spécifique" if request.question_id else "Conversation complète"
        }
        
        # Si un ID de question spécifique est fourni
        if request.question_id:
            question = db.query(Question).filter(
                Question.id == request.question_id,
                Question.conversation_id == conversation.id
            ).first()
            
            if not question:
                raise HTTPException(status_code=404, detail="Question non trouvée")
            
            response = db.query(Response).filter(
                Response.question_id == question.id
            ).first()
            
            if not response:
                raise HTTPException(status_code=404, detail="Réponse non trouvée")
            
            # Ajouter le contenu de la question et de la réponse
            content = f"Question: {question.question_text}\n\n"
            content += f"Réponse: {response.response_text}"
            
            # Ajouter les sources si disponibles et demandées
            if request.include_sources and response.sources:
                sources = response.sources
        
        # Si on veut l'historique complet de la conversation
        elif request.include_question_history and conversation:
            questions = db.query(Question).filter(
                Question.conversation_id == conversation.id
            ).order_by(Question.created_at).all()
            
            content += f"Historique de la conversation: {conversation.title}\n\n"
            
            for question in questions:
                content += f"Question: {question.question_text}\n\n"
                
                response = db.query(Response).filter(
                    Response.question_id == question.id
                ).first()
                
                if response:
                    content += f"Réponse: {response.response_text}\n\n"
                    
                    # Collecter toutes les sources
                    if request.include_sources and response.sources:
                        for source in response.sources:
                            if source not in sources:
                                sources.append(source)
                
                content += "----------------------------------------\n\n"
                
        else:
            # Si aucune conversation ou question spécifique n'est fournie
            raise HTTPException(status_code=400, detail="Vous devez spécifier un conversation_id")
        
        # Générer le document selon le format demandé
        file_path = None
        filename = None
        
        if request.format.lower() == "pdf":
            file_path = document_generator.generate_pdf(title, content, metadata, sources)
            filename = os.path.basename(file_path)
        elif request.format.lower() == "docx":
            file_path = document_generator.generate_word(title, content, metadata, sources)
            filename = os.path.basename(file_path)
        else:
            raise HTTPException(status_code=400, detail="Format de document non supporté. Utilisez 'pdf' ou 'docx'")
        
        # Préparer l'URL pour le téléchargement
        document_url = f"/api/document-generator/download/{filename}"
        
        return DocumentResponse(
            filename=filename,
            url=document_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur lors de la génération du document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du document: {str(e)}")

@router.get("/download/{filename}")
async def download_document(
    filename: str,
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Télécharge un document généré précédemment.
    """
    try:
        file_path = os.path.join(document_generator.output_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Déterminer le type de contenu en fonction de l'extension
        content_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=content_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement du document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement du document: {str(e)}")
