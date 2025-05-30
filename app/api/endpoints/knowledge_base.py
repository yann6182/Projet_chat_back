# app/api/endpoints/knowledge_base.py
from fastapi import APIRouter, HTTPException
from app.schemas.knowledge_base import SearchRequest, SearchResponse, LegalDocument
from app.services.retrieval_service import RetrievalService
from app.services.knowledge_base_service import search_knowledge_base


router = APIRouter(prefix="/knowledge", tags=["knowledge"])
retrieval_service = RetrievalService()

@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """
    Recherche des informations dans la base de connaissances juridiques.
    """
    try:
        results = await retrieval_service.retrieve_relevant_documents(request.query, request.max_results)
        return SearchResponse(results=results, total_count=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update", response_model=dict)
async def update_knowledge_base(document: LegalDocument):
    """
    Ajoute un nouveau document à la base de connaissances.
    """
    try:
        success = await retrieval_service.update_knowledge_base(document)
        if success:
            return {"message": "Document ajouté avec succès à la base de connaissances"}
        else:
            raise HTTPException(status_code=500, detail="Échec de l'ajout du document")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/search/")
def search_laws(query: str):
    results = search_knowledge_base(query)
    return {"documents": results}