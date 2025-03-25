from pydantic import BaseModel
from typing import List, Optional, Dict

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    conversation_id: str  # uuid de la conversation
    context: Optional[Dict[str, str]] = None

    class Config:
        orm_mode = True
