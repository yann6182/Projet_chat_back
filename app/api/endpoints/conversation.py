from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.db.database import get_db
from app.models import model
from app.schemas import conversation as schemas
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["conversations"])
chat_service = ChatService()

@router.post("/", response_model=schemas.ConversationResponse)
def create_conversation(convo: schemas.ConversationCreate, db: Session = Depends(get_db)):
    new_convo = model.Conversation(user_id=convo.user_id)
    db.add(new_convo)
    db.commit()
    db.refresh(new_convo)
    return new_convo

@router.get("/{conversation_id}", response_model=schemas.ConversationResponse)
def get_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    convo = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@router.get("/", response_model=List[schemas.ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(model.Conversation).all()

# Ajouter une question à une conversation
@router.post("/{conversation_id}/questions", response_model=schemas.QuestionResponse)
def add_question(conversation_id: UUID, question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    convo = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    new_question = model.Question(
        conversation_id=conversation_id,
        question_text=question.question_text,
        user_id=question.user_id
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question

# Ajouter une réponse à une question
@router.post("/questions/{question_id}/responses", response_model=schemas.ResponseResponse)
def add_response(question_id: int, response: schemas.ResponseCreate, db: Session = Depends(get_db)):
    question = db.query(model.Question).filter(model.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    new_response = model.Response(
        question_id=question_id,
        response_text=response.response_text
    )
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    return new_response

# Ajouter une question et générer une réponse automatiquement
@router.post("/{conversation_id}/questions/auto-response", response_model=schemas.ResponseResponse)
def ask_and_generate(conversation_id: UUID, question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    convo = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    new_question = model.Question(
        conversation_id=conversation_id,
        question_text=question.question_text,
        user_id=question.user_id
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    # Générer une réponse avec le service IA
    chat_response = chat_service.nlp_model(
        f"Question : {question.question_text}\nRéponds de manière claire et concise.",
        max_length=150,
        do_sample=True,
        temperature=0.7,
        top_p=0.9
    )
    generated_text = chat_response[0]['generated_text'] if chat_response else "Réponse non disponible."

    new_response = model.Response(
        question_id=new_question.id,
        response_text=generated_text
    )
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    return new_response

# Récupérer l'historique complet d'une conversation
@router.get("/{conversation_id}/history")
def get_conversation_history(conversation_id: UUID, db: Session = Depends(get_db)):
    convo = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = []
    for q in convo.questions:
        entry = {
            "question_id": q.id,
            "question_text": q.question_text,
            "created_at": q.created_at,
            "response": None
        }
        if q.responses:
            entry["response"] = {
                "response_text": q.responses[0].response_text,
                "created_at": q.responses[0].created_at
            }
        history.append(entry)

    return {"conversation_id": conversation_id, "user_id": convo.user_id, "history": history}
