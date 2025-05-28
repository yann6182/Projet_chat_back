import os
import fitz  # PyMuPDF
import logging
from typing import List, Dict
from app.services.document_chunker import DocumentChunker

logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self, docs_path: str = "./data", chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialise le chargeur de documents.
        
        Args:
            docs_path: Chemin vers le répertoire contenant les documents
            chunk_size: Taille des chunks pour le découpage
            chunk_overlap: Chevauchement entre les chunks
        """
        self.docs_path = docs_path
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        logger.info(f"DocumentLoader initialisé avec chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")

    def load_documents(self) -> List[Dict]:
        """
        Charge les fichiers PDF et TXT depuis le répertoire, les découpe et retourne une liste de chunks.
        """
        documents = []
        failed_files = []
        
        # Vérifier si le répertoire existe
        if not os.path.exists(self.docs_path):
            logger.warning(f"Le répertoire {self.docs_path} n'existe pas. Création...")
            try:
                os.makedirs(self.docs_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Erreur lors de la création du répertoire: {str(e)}")
                return []
        
        # Parcourir les fichiers du répertoire
        for filename in os.listdir(self.docs_path):
            filepath = os.path.join(self.docs_path, filename)
            
            try:
                if filename.lower().endswith(".pdf"):
                    documents.extend(self._load_pdf(filepath))
                elif filename.lower().endswith(".txt"):
                    documents.extend(self._load_txt(filepath))
                # On pourrait ajouter d'autres formats ici (.docx, .md, etc.)
            except Exception as e:
                logger.error(f"Erreur lors du chargement du fichier {filename}: {str(e)}")
                failed_files.append(filename)
        
        # Chunker les documents
        chunked_documents = self.chunker.process_documents(documents)
        
        logger.info(f"📄 {len(documents)} documents chargés, découpés en {len(chunked_documents)} chunks")
        if failed_files:
            logger.warning(f"⚠️ {len(failed_files)} fichiers n'ont pas pu être chargés: {', '.join(failed_files)}")
            
        return chunked_documents

    def _load_pdf(self, filepath: str) -> List[Dict]:
        """
        Charge un fichier PDF et extrait le texte par pages.
        """
        doc_parts = []
        doc = fitz.open(filepath)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                doc_parts.append({
                    "content": text.strip(),
                    "source": os.path.basename(filepath),
                    "page": page_num + 1,
                    "file_path": filepath
                })

        return doc_parts

    def _load_txt(self, filepath: str) -> List[Dict]:
        """
        Charge un fichier texte.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                
            return [{
                "content": text.strip(),
                "source": os.path.basename(filepath),
                "page": None,
                "file_path": filepath
            }]
        except UnicodeDecodeError:
            # Essayer avec une autre encodage
            try:
                with open(filepath, "r", encoding="latin-1") as f:
                    text = f.read()
                return [{
                    "content": text.strip(),
                    "source": os.path.basename(filepath),
                    "page": None,
                    "file_path": filepath
                }]
            except Exception as e:
                logger.error(f"Impossible de lire le fichier {filepath}: {str(e)}")
                return []

# Exemple d'utilisation
if __name__ == "__main__":
    loader = DocumentLoader("./data")
    docs = loader.load_documents()
    print(f"📄 {len(docs)} documents chargés")
    print(docs[0] if docs else "Aucun document trouvé.")
