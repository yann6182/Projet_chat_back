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

class DocumentInfo(BaseModel):
    """Information sur un document généré automatiquement."""
    filename: str
    url: str
    format: str  # "pdf" ou "docx"
    
class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    conversation_id: str  # uuid de la conversation
    context: Optional[Dict[str, str]] = None
    excerpts: Optional[List[Excerpt]] = None
    generated_document: Optional[DocumentInfo] = None  # Informations sur le document généré automatiquement

    class Config:
        from_attributes = True
