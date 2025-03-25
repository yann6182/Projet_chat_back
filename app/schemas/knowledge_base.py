from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class LegalDocument(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str] = []
    source: str
    date_published: Optional[datetime] = None
    relevance_score: Optional[float] = None

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict] = None
    max_results: int = 5

class SearchResponse(BaseModel):
    results: List[LegalDocument]
    total_count: int
    query: str