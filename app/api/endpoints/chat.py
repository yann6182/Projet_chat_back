from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid 
import logging
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.schema import ConversationSchema, ConversationWithHistory
from app.models.model import Conversation, User, Question, Response
from app.db.database import get_db,SessionLocal
from app.services.chat_service import ChatService
from app.api.endpoints.auth import get_current_user, get_optional_user  # Importer les fonctions d'authentification

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/new-conversation", response_model=ChatResponse)
async def create_new_conversation(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Crée une nouvelle conversation avec un titre généré automatiquement par l'IA.
    """
    try:
        # Générer un nouvel ID de conversation unique
        conversation_id = str(uuid.uuid4())
        
        # Déterminer la catégorie et générer le titre automatiquement
        category = chat_service._determine_category(request.query)
        title = chat_service._generate_title(request.query)

        # Enregistrer la conversation en base de données
        db_conversation = Conversation(
            uuid=conversation_id,
            user_id=current_user.id,
            category=category,
            title=title  # Titre généré automatiquement
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        return ChatResponse(
            answer="Nouvelle conversation créée avec succès.",
            sources=[],
            conversation_id=conversation_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/query", response_model=ChatResponse)
async def process_query(
    request: ChatRequest,
    conversation_id: Optional[str] = None,  # Ajout de l'ID de la conversation
    current_user: User = Depends(get_current_user),  # Authentification obligatoire
    db: Session = Depends(get_db)
):
    """
    Traite une requête utilisateur et génère une réponse juridique.
    Si aucun conversation_id n'est fourni, une nouvelle conversation est automatiquement créée.
    L'utilisateur doit être connecté pour utiliser cette fonctionnalité.
    
    La requête peut inclure des documents contextuels (context_documents) fournis par le front-end
    pour enrichir la réponse. Ces documents seront utilisés en plus des documents trouvés
    dans la base de connaissances vectorielle.
    """
    try:
        # Si aucun ID de conversation n'est fourni, créer automatiquement une nouvelle conversation
        if conversation_id is None:
            # Générer un nouvel ID de conversation unique
            conversation_id = str(uuid.uuid4())
            
            # Déterminer la catégorie et générer le titre automatiquement
            category = chat_service._determine_category(request.query)
            title = chat_service._generate_title(request.query)

            # Enregistrer la conversation en base de données
            db_conversation = Conversation(
                uuid=conversation_id,
                user_id=current_user.id,
                category=category,
                title=title  # Titre généré automatiquement
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
            logging.info(f"Nouvelle conversation créée automatiquement: {conversation_id}")

        # L'utilisateur est toujours connecté ici
        response = await chat_service.process_query(request, user_id=current_user.id, conversation_id=conversation_id)
        return response
    except Exception as e:
        if conversation_id is None:
            db.rollback()  # Annuler la création de conversation en cas d'échec
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
    
    Comme pour /query, la requête peut inclure des documents contextuels (context_documents) 
    fournis par le front-end pour enrichir la réponse de l'IA.
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
    print(f"Tentative d'accès à l'historique de la conversation: {conversation_id}")
    print(f"Utilisateur: {current_user.id if current_user else 'Non authentifié'}")
    
    # Vérifier si la conversation appartient à l'utilisateur actuel
    if current_user:
        conversation = db.query(Conversation).filter(
            Conversation.uuid == conversation_id
        ).first()
        
        if not conversation:
            print(f"Conversation {conversation_id} introuvable")
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
            
        print(f"Conversation trouvée: {conversation.id}, user_id: {conversation.user_id}")
        
        if conversation and conversation.user_id is not None:
            if conversation.user_id != current_user.id:
                print(f"Accès refusé: conversation appartient à l'utilisateur {conversation.user_id}")
                raise HTTPException(
                    status_code=403, 
                    detail="Vous n'avez pas accès à cette conversation"
                )
    
    # Récupérer l'historique
    history = chat_service.get_conversation_history(conversation_id)
    print(f"Historique récupéré: {len(history) if history else 0} messages")
    
    if not history:
        raise HTTPException(status_code=404, detail="Historique de conversation non trouvé")
    
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
    
@router.delete("/delete/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authentification obligatoire
):
    """
    Supprime une conversation et toutes ses questions/réponses associées.
    """
    try:
        # Vérifier si la conversation existe
        conversation = db.query(Conversation).filter(Conversation.uuid == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

        # Vérifier si l'utilisateur est autorisé à supprimer cette conversation
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Vous n'avez pas l'autorisation de supprimer cette conversation")

        # Supprimer les questions et réponses associées
        db.query(Response).filter(Response.conversation_id == conversation.id).delete()
        db.query(Question).filter(Question.conversation_id == conversation.id).delete()

        # Supprimer la conversation
        db.delete(conversation)
        db.commit()

        return {"message": "Conversation supprimée avec succès"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de la conversation: {str(e)}")