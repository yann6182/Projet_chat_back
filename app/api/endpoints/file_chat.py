"""
Endpoint pour gérer l'upload de fichier avec une question.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
import uuid
import logging
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse, DocumentContext
from app.models.model import User
from app.db.database import SessionLocal
from app.services.chat_service import ChatService
from app.services.file_service import FileService
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/file-chat", tags=["file-chat"])
chat_service = ChatService()
file_service = FileService()

@router.post("/query", response_model=ChatResponse)
async def process_file_query(
    query: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user)
):
    """
    Traite une requête utilisateur accompagnée de fichiers (optionnels).
    Les fichiers sont analysés et leur contenu est utilisé pour enrichir le contexte de la question.
    
    - **query**: La question de l'utilisateur
    - **conversation_id**: (Optionnel) L'ID de la conversation existante
    - **files**: (Optionnel) Liste des fichiers à analyser (PDF, DOCX, TXT, etc.)
    
    Retourne une réponse enrichie basée sur le contenu des fichiers et la base de connaissance.
    """
    try:
        # Créer une liste pour stocker les documents extraits des fichiers
        context_documents = []
        
        # Traiter les fichiers s'il y en a
        if files:
            for file in files:
                try:
                    # Extraire le texte du fichier
                    doc_info = await file_service.extract_text_from_upload(file)
                    
                    # Créer un document contextuel
                    doc = DocumentContext(
                        content=doc_info['content'],
                        source=doc_info['source'],
                        mime_type=doc_info['mime_type'],
                        size=doc_info['size']
                    )
                    context_documents.append(doc)
                except Exception as e:
                    logging.error(f"Erreur lors du traitement du fichier {file.filename}: {str(e)}")
        
        # Créer la requête avec les documents extraits
        chat_request = ChatRequest(
            query=query,
            conversation_id=conversation_id,
            context_documents=context_documents
        )
        
        # Traiter la requête avec le service de chat
        response = await chat_service.process_query(chat_request, user_id=current_user.id, conversation_id=conversation_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue/{conversation_id}", response_model=ChatResponse)
async def continue_conversation_with_files(
    conversation_id: str,
    query: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user)
):
    """
    Continue une conversation existante avec de nouveaux fichiers.
    Vérifie que l'utilisateur a accès à cette conversation.
    
    - **conversation_id**: L'ID de la conversation à continuer
    - **query**: La question de l'utilisateur
    - **files**: (Optionnel) Liste des fichiers à analyser (PDF, DOCX, TXT, etc.)
    """
    db = SessionLocal()
    try:
        # Vérifier si la conversation appartient à l'utilisateur actuel
        from app.models.model import Conversation
        conversation = db.query(Conversation).filter(
            Conversation.uuid == conversation_id
        ).first()
        
        if conversation and conversation.user_id is not None:
            if conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail="Vous n'avez pas accès à cette conversation"
                )
        
        # Traiter les fichiers s'il y en a
        context_documents = []
        if files:
            for file in files:
                try:
                    # Extraire le texte du fichier
                    doc_info = await file_service.extract_text_from_upload(file)
                    
                    # Créer un document contextuel
                    doc = DocumentContext(
                        content=doc_info['content'],
                        source=doc_info['source'],
                        mime_type=doc_info['mime_type'],
                        size=doc_info['size']
                    )
                    context_documents.append(doc)
                except Exception as e:
                    logging.error(f"Erreur lors du traitement du fichier {file.filename}: {str(e)}")
        
        # Créer la requête avec les documents extraits
        chat_request = ChatRequest(
            query=query,
            conversation_id=conversation_id,
            context_documents=context_documents
        )
        
        # Traiter la requête
        response = await chat_service.process_query(chat_request, conversation_id=conversation_id, user_id=current_user.id)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
