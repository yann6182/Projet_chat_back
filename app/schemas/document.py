# app/schemas/document.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str = "uploaded"

class DocumentAnalysisRequest(BaseModel):
    document_id: str

class SpellingError(BaseModel):
    word: str
    position: Dict[str, int]
    suggestions: List[str]

class GrammarError(BaseModel):
    text: str
    position: Dict[str, int]
    message: str
    suggestions: List[str]

class LegalComplianceIssue(BaseModel):
    text: str
    position: Dict[str, int]
    issue_type: str
    description: str
    recommendation: str

class DocumentAnalysisResponse(BaseModel):
    document_id: str
    filename: str
    spelling_errors: List[SpellingError] = []
    grammar_errors: List[GrammarError] = []
    legal_compliance_issues: List[LegalComplianceIssue] = []
    overall_compliance_score: Optional[float] = None
    suggestions: List[str] = []

class DocumentResponse(BaseModel):
    filename: str
    filepath: str
    size: int
    description: Optional[str] = None
