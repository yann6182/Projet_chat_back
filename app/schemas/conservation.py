from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ConversationBase(BaseModel):
    uuid: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    uuid: str
    created_at: datetime

    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    question_text: str
    conversation_id: int

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ResponseBase(BaseModel):
    response_text: str
    conversation_id: int
    question_id: Optional[int] = None

class ResponseCreate(ResponseBase):
    pass

class ResponseResponse(ResponseBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True