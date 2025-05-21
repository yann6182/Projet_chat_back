import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import pickle

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "./vector_store/index.faiss"):
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(384) 
        self.meta_data: List[Dict] = []  

    def build_index(self, documents: List[Dict]):
        texts = [doc["content"] for doc in documents]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        self.index.add(np.array(embeddings).astype("float32"))
        self.meta_data.extend(documents)

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path.replace(".faiss", "_meta.pkl"), "wb") as f:
            pickle.dump(self.meta_data, f)

        print(f"✅ Index construit avec {len(texts)} documents.")

    def load_index(self):
        if not os.path.exists(self.index_path):
            print("⚠️ Aucun index FAISS trouvé. Veuillez indexer des documents en premier.")
            return

        self.index = faiss.read_index(self.index_path)
        with open(self.index_path.replace(".faiss", "_meta.pkl"), "rb") as f:
            self.meta_data = pickle.load(f)

    def search(self, query: str, k: int = 3) -> List[Dict]:
        if not self.meta_data or not self.index.is_trained or self.index.ntotal == 0:
            return []

        query_vec = self.model.encode([query])
        D, I = self.index.search(np.array(query_vec).astype("float32"), k)

        if len(I[0]) == 0 or I[0][0] == -1:
            return []

        return [self.meta_data[i] for i in I[0] if i < len(self.meta_data)]


if __name__ == "__main__":
    from app.services.document_loader import DocumentLoader

    loader = DocumentLoader("./data")
    docs = loader.load_documents()

    service = EmbeddingService()
    service.build_index(docs)

    results = service.search("statuts des associations")
    print("Résultats pertinents :")
    for r in results:
        print("-", r["source"], "|", r["content"][:100])
