# app/api/endpoints/chat.py
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()

@router.post("/query", response_model=ChatResponse)
async def process_query(request: ChatRequest):
    """
    Traite une requête utilisateur et génère une réponse juridique.
    """
    try:
        response = await chat_service.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """
    Récupère l'historique d'une conversation.
    """
    history = chat_service.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    return {"conversation_id": conversation_id, "history": history}

@router.delete("/history/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Efface l'historique d'une conversation.
    """
    success = chat_service.clear_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    return {"message": "Conversation effacée avec succès"}
