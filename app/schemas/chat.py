from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class DocumentContext(BaseModel):
    """Document contextuel fourni avec la requête pour enrichir la réponse."""
    content: str
    source: str
    page: Optional[int] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None

class Excerpt(BaseModel):
    content: str
    source: str
    page: Optional[int] = None

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    context_documents: Optional[List[DocumentContext]] = Field(default_factory=list, 
                                                             description="Documents contextuels fournis par le front-end")

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    conversation_id: str  # uuid de la conversation
    context: Optional[Dict[str, str]] = None
    excerpts: Optional[List[Excerpt]] = None

    class Config:
        from_attributes = True
