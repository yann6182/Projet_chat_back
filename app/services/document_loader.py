import os
import fitz  # PyMuPDF
from typing import List

class DocumentLoader:
    def __init__(self, docs_path: str = "./data"):
        self.docs_path = docs_path

    def load_documents(self) -> List[dict]:
        """
        Charge les fichiers PDF et TXT depuis le répertoire, retourne une liste de chunks.
        """
        documents = []

        for filename in os.listdir(self.docs_path):
            filepath = os.path.join(self.docs_path, filename)

            if filename.lower().endswith(".pdf"):
                documents.extend(self._load_pdf(filepath))
            elif filename.lower().endswith(".txt"):
                documents.extend(self._load_txt(filepath))

        return documents

    def _load_pdf(self, filepath: str) -> List[dict]:
        doc_chunks = []
        doc = fitz.open(filepath)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                doc_chunks.append({
                    "content": text.strip(),
                    "source": os.path.basename(filepath),
                    "page": page_num + 1
                })

        return doc_chunks

    def _load_txt(self, filepath: str) -> List[dict]:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        return [{
            "content": text.strip(),
            "source": os.path.basename(filepath),
            "page": None
        }]

# Exemple d'utilisation
if __name__ == "__main__":
    loader = DocumentLoader("./data")
    docs = loader.load_documents()
    print(f"📄 {len(docs)} documents chargés")
    print(docs[0] if docs else "Aucun document trouvé.")
