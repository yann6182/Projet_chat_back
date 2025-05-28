from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ItemBase(BaseModel):
    name: str

class ItemCreate(ItemBase):
    pass

class ItemSchema(ItemBase):
    id: int
    
    class Config:
        from_attributes = True

class QuestionSchema(BaseModel):
    user_id: int
    question_text: str

    class Config:
        from_attributes = True

class ResponseSchema(BaseModel):
    question_id: int
    response_text: str

    class Config:
        from_attributes = True

# Nouveaux schémas pour l'authentification
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSchema(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

# Nouveaux schémas pour les conversations
class ConversationBase(BaseModel):
    title: Optional[str] = "Nouvelle conversation"
    category: Optional[str] = "other"  # Ajouter la catégorie


class ConversationCreate(ConversationBase):
    pass

class ConversationSchema(ConversationBase):
    id: int
    uuid: UUID
    user_id: int
    category: str  # Ajout de la catégorie
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Schémas améliorés pour les questions et réponses
class QuestionCreate(BaseModel):
    conversation_id: int
    question_text: str

class QuestionWithResponseSchema(QuestionSchema):
    id: int
    created_at: datetime
    responses: List[ResponseSchema] = []
    
    class Config:
        from_attributes = True

class ResponseCreate(BaseModel):
    question_id: int
    response_text: str

class ConversationWithHistory(ConversationSchema):
    questions: List[QuestionWithResponseSchema] = []
    
    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBase(KnowledgeBaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    documents: List[Document] = []

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    question_text: str

    class Config:
        from_attributes = True


class Question(QuestionBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResponseBase(BaseModel):
    response_text: str

    class Config:
        from_attributes = True


class Response(ResponseBase):
    id: int
    conversation_id: int
    question_id: int
    created_at: datetime

    class Config:
        from_attributes = True