from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid 
import logging
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.schema import ConversationSchema, ConversationWithHistory
from app.models.model import Conversation, User
from app.db.database import get_db,SessionLocal
from app.services.chat_service import ChatService
from app.api.endpoints.auth import get_current_user, get_optional_user  # Importer les fonctions d'authentification

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/new-conversation", response_model=ChatResponse)
async def create_new_conversation(
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Crée une nouvelle conversation vide pour l'utilisateur.
    Retourne l'ID de la nouvelle conversation.
    L'utilisateur doit être connecté pour utiliser cette fonctionnalité.
    """
    try:
        # Générer un nouvel ID de conversation unique
        conversation_id = str(uuid.uuid4())
        
        # Enregistrer la conversation vide en base de données
        db = SessionLocal()
        try:
            # Créer une nouvelle conversation associée à l'utilisateur actuel
            db_conversation = Conversation(
                uuid=conversation_id,
                user_id=current_user.id,
                category="other"  # Catégorie par défaut
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
        finally:
            db.close()
        
        # Retourner les infos de la nouvelle conversation avec le champ answer requis
        return {
            "conversation_id": conversation_id,
            "message": "Nouvelle conversation créée avec succès",
            "answer": "Bonjour, comment puis-je vous aider aujourd'hui?",  # Champ requis
            "greeting": "Bonjour, comment puis-je vous aider aujourd'hui?"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/query", response_model=ChatResponse)
async def process_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Traite une requête utilisateur et génère une réponse juridique.
    Un nouveau conversation_id est généré automatiquement.
    L'utilisateur doit être connecté pour utiliser cette fonctionnalité.
    """
    try:
        # L'utilisateur est toujours connecté ici
        response = await chat_service.process_query(request, user_id=current_user.id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue/{conversation_id}", response_model=ChatResponse)
async def continue_conversation(
    conversation_id: str, 
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Continue une conversation existante identifiée par son ID.
    Vérifie que l'utilisateur a accès à cette conversation.
    L'utilisateur doit être connecté pour utiliser cette fonctionnalité.
    """
    try:
        # Vérifier si la conversation appartient à l'utilisateur actuel
        conversation = db.query(Conversation).filter(
            Conversation.uuid == conversation_id
        ).first()
        
        if conversation and conversation.user_id is not None:
            if conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail="Vous n'avez pas accès à cette conversation"
                )
        
        response = await chat_service.process_query(request, conversation_id=conversation_id, user_id=current_user.id)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Récupère l'historique d'une conversation.
    Vérifie que l'utilisateur a accès à cette conversation.
    """
    # Vérifier si la conversation appartient à l'utilisateur actuel
    if current_user:
        conversation = db.query(Conversation).filter(
            Conversation.uuid == conversation_id
        ).first()
        
        if conversation and conversation.user_id is not None:
            if conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail="Vous n'avez pas accès à cette conversation"
                )
    
    # Récupérer l'historique
    history = chat_service.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    return {"conversation_id": conversation_id, "history": history}

@router.delete("/history/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Efface l'historique d'une conversation.
    Vérifie que l'utilisateur a accès à cette conversation.
    """
    # Vérifier si la conversation appartient à l'utilisateur actuel
    if current_user:
        conversation = db.query(Conversation).filter(
            Conversation.uuid == conversation_id
        ).first()
        
        if conversation and conversation.user_id is not None:
            if conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail="Vous n'avez pas accès à cette conversation"
                )
    
    success = chat_service.clear_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    return {"message": "Conversation effacée avec succès"}

# Ces endpoints nécessitent une authentification complète
@router.get("/my-conversations", response_model=List[ConversationSchema])
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Récupère toutes les conversations de l'utilisateur connecté.
    """
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).all()
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )

# Les endpoints suivants devraient nécessiter des droits d'administration
@router.get("/conversations", response_model=List[ConversationSchema])
def get_all_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authentification requise
):
    """
    Récupère toutes les conversations avec leur historique.
    Réservé aux administrateurs.
    """
    # Vérifier si l'utilisateur a les droits d'admin (à implémenter)
    # if not current_user.is_admin:
    #    raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    try:
        conversations = db.query(Conversation).all()
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )

# Remplacer les endpoints avec user_id par des endpoints plus sécurisés
@router.get("/conversations/category/{category}", response_model=List[ConversationSchema])
def get_my_conversations_by_category(
    category: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les conversations de l'utilisateur connecté pour une catégorie spécifique.
    """
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.category == category
        ).all()
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )

@router.get("/my-statistics")
def get_my_conversation_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère des statistiques sur les conversations de l'utilisateur connecté par catégorie.
    """
    from sqlalchemy import func
    
    try:
        stats = db.query(Conversation.category, func.count(Conversation.id))\
                .filter(Conversation.user_id == current_user.id)\
                .group_by(Conversation.category)\
                .all()
                
        # Convertir en dictionnaire
        statistics = {category: count for category, count in stats}
        
        # Ajouter le nombre total de conversations
        total_count = sum(statistics.values()) if statistics else 0
        
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "total_conversations": total_count,
            "by_category": statistics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )

# Conserver ces endpoints pour l'administration si nécessaire
@router.get("/admin/conversations/{user_id}", response_model=List[ConversationSchema])
def get_user_conversations(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [ADMIN] Récupère toutes les conversations d'un utilisateur spécifique.
    """
    # Vérifier si l'utilisateur est admin
    # if not current_user.is_admin:
    #    raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    try:
        conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )