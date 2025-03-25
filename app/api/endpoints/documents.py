# app/api/endpoints/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List
from app.schemas.document import DocumentAnalysisRequest, DocumentAnalysisResponse, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.services.document_service import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])
document_service = DocumentService()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Télécharge un document pour analyse.
    """
    try:
        document_id = await document_service.save_document(file.file, file.filename)
        return DocumentUploadResponse(document_id=document_id, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Analyse un document téléchargé pour vérifier son orthographe, sa grammaire et sa conformité légale.
    """
    try:
        analysis_result = await document_service.analyze_document(request.document_id)
        return analysis_result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    result = process_document(content, file.filename)
    return {"message": "Analyse terminée", "result": result}