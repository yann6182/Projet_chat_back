from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
import shutil
from app.services.document_loader import DocumentLoader
from app.services.embedding_service import EmbeddingService

router = APIRouter()
UPLOAD_DIR = "./data"

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Recharger les documents et reconstruire l'index
        loader = DocumentLoader(UPLOAD_DIR)
        docs = loader.load_documents()

        embedder = EmbeddingService()
        embedder.build_index(docs)

        return JSONResponse(content={"message": f"✅ {file.filename} uploadé et indexé avec succès."}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
