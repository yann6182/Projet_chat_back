import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.api.endpoints import users, chat, documents, knowledge_base, auth, file_chat

Base.metadata.create_all(bind=engine)
# Création de l'application FastAPI
app = FastAPI(
    title="Juridica API",
    description="API pour le projet Juridica",
    version="0.1.0"
)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # 8000 par défaut en local
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)



# Configuration CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-CSRFToken"],
)

@app.get("/")
async def root():
    return {"message": "Bienvenue sur mon API FastAPI"}

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(knowledge_base.router)
app.include_router(auth.router)
app.include_router(file_chat.router)