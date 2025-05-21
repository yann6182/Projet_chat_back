from typing import List, Dict, Any, Optional
import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from app.schemas.knowledge_base import LegalDocument

class RetrievalService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.vector_store_path = "data/vector_store"
        self.legal_docs_path = "data/legal_docs"
        
        self.initialize_vector_store()
        
    def initialize_vector_store(self):
        """
        Initialise ou charge la base de données vectorielle pour la recherche de similarité.
        """
        if os.path.exists(self.vector_store_path):
            self.vector_store = FAISS.load_local(self.vector_store_path, self.embeddings)
        else:
            documents = self.load_legal_documents()
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                texts = text_splitter.split_documents(documents)
                self.vector_store = FAISS.from_documents(texts, self.embeddings)
                os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
                self.vector_store.save_local(self.vector_store_path)
            else:
                self.vector_store = FAISS.from_texts(["Document placeholder"], self.embeddings)
    
    def load_legal_documents(self) -> List[Any]:
        """
        Charge les documents juridiques à partir du répertoire des documents légaux.
        
        Returns:
            Une liste de documents chargés.
        """
        documents = []
        
        if not os.path.exists(self.legal_docs_path):
            os.makedirs(self.legal_docs_path, exist_ok=True)
            return documents
        
        for filename in os.listdir(self.legal_docs_path):
            file_path = os.path.join(self.legal_docs_path, filename)
            
            if os.path.isdir(file_path):
                continue
                
            try:
                if filename.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
                elif filename.endswith('.docx') or filename.endswith('.doc'):
                    loader = Docx2txtLoader(file_path)
                    documents.extend(loader.load())
                elif filename.endswith('.txt'):
                    loader = TextLoader(file_path)
                    documents.extend(loader.load())
            except Exception as e:
                print(f"Erreur lors du chargement du document {filename}: {e}")
                
        return documents
    
    async def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> List[LegalDocument]:
        """
        Récupère les documents juridiques les plus pertinents pour une requête donnée.
        
        Args:
            query: La requête utilisateur
            top_k: Le nombre maximum de documents à récupérer
            
        Returns:
            Une liste de documents juridiques pertinents
        """
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        legal_documents = []
        for doc, score in docs_with_scores:
            legal_doc = LegalDocument(
                id=doc.metadata.get("id", "unknown"),
                title=doc.metadata.get("title", "Sans titre"),
                content=doc.page_content,
                category=doc.metadata.get("category", "Général"),
                tags=doc.metadata.get("tags", []),
                source=doc.metadata.get("source", "Base de connaissances interne"),
                relevance_score=float(1.0 - score/10)  # Convertir le score en une mesure de pertinence
            )
            legal_documents.append(legal_doc)
            
        return legal_documents
    
    async def augment_query(self, query: str, documents: List[LegalDocument]) -> str:
        """
        Augmente la requête utilisateur avec le contenu des documents pertinents.
        
        Args:
            query: La requête utilisateur
            documents: Les documents pertinents récupérés
            
        Returns:
            La requête augmentée
        """
        context = ""
        for doc in documents:
            context += f"\nSource: {doc.source}\n{doc.content}\n"
            
        augmented_query = f"""
        Question: {query}
        
        Contexte juridique:
        {context}
        
        Réponse:
        """
        
        return augmented_query
    def update_index(self, new_documents: List[str]):
        """Ajoute de nouveaux documents à la base FAISS."""
        texts = [doc.page_content for doc in new_documents]
        new_vectors = self.embedding_model.embed(texts)
        self.vector_db.add_documents(texts, new_vectors)
        self.vector_db.save_local("faiss_index")

    
    async def update_knowledge_base(self, document: LegalDocument) -> bool:
        """
        Ajoute un nouveau document à la base de connaissances.
        
        Args:
            document: Le document juridique à ajouter
            
        Returns:
            True si l'ajout a réussi, False sinon
        """
        try:
            self.vector_store.add_texts(
                texts=[document.content],
                metadatas=[{
                    "id": document.id,
                    "title": document.title,
                    "category": document.category,
                    "tags": document.tags,
                    "source": document.source
                }]
            )
            
            self.vector_store.save_local(self.vector_store_path)
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'ajout du document à la base de connaissances: {e}")
            return False
    
    async def query_external_provider(self, query: str) -> List[LegalDocument]:
        """
        Interroge un fournisseur externe de données juridictionnelles.
        
        Args:
            query: La requête utilisateur
            
        Returns:
            Une liste de documents juridiques provenant de sources externes
        """
        return []
