from app.services.retrieval_service import RetrievalService

retrieval_service = RetrievalService()

def search_knowledge_base(query: str):
    results = retrieval_service.search_documents(query, k=5)
    return results
