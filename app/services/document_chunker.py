import re
from typing import List, Dict, Optional, Any, Union
import logging
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentChunker:
    """
    Service responsable du découpage intelligent des documents en chunks pour l'indexation.
    Optimisé pour les documents juridiques avec préservation de la structure et des métadonnées.
    """
    def __init__(
        self, 
        chunk_size: int = 300,  # Taille cible en tokens (~400 caractères)
        chunk_overlap: int = 50,  # Chevauchement en tokens (~65 caractères)
        separators: List[str] = None  # Séparateurs pour découpage intelligent
    ):
        """
        Initialise le service de chunking optimisé pour les documents juridiques.
        
        Args:
            chunk_size: Taille approximative (en tokens) de chaque chunk
            chunk_overlap: Nombre de tokens qui se chevauchent entre les chunks
            separators: Liste des séparateurs à utiliser pour le découpage intelligent
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Séparateurs optimisés pour les documents juridiques
        # Ordre du plus significatif au moins significatif
        self.separators = separators or [
            "\n\n\n",  # Sections très distinctes
            "\n\n",    # Paragraphes
            "\n",      # Lignes
            ". ",      # Phrases
            "; ",      # Éléments de liste ou clauses
            ", ",      # Éléments d'énumération
            " ",       # Dernier recours : mots
            ""         # Caractères individuels si nécessaire
        ]
        
        # Initialisation du text splitter de LangChain
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size * 4,  # ~4 caractères par token en français
            chunk_overlap=self.chunk_overlap * 4,
            separators=self.separators,
            keep_separator=True
        )
    
    def create_chunks(self, document: Union[Dict, Document]) -> List[Dict]:
        """
        Découpe un document en chunks optimisés avec chevauchement intelligent.
        Préserve les métadonnées du document original.
        
        Args:
            document: Le document à chunker (avec contenu et métadonnées)
            
        Returns:
            Liste de chunks avec leurs métadonnées préservées et enrichies
        """
        # Extraire le contenu et les métadonnées selon le format d'entrée
        if isinstance(document, Document):
            content = document.page_content
            metadata = document.metadata.copy() if hasattr(document, 'metadata') else {}
        else:
            content = document.get("content", "")
            metadata = document.get("metadata", {}).copy() if document.get("metadata") else {}
            
            # Extraire les métadonnées directes si présentes
            if "source" in document and "source" not in metadata:
                metadata["source"] = document["source"]
            if "page" in document and "page" not in metadata:
                metadata["page"] = document["page"]
        
        # Si le document est vide, retourner une liste vide
        if not content or not content.strip():
            logger.warning(f"Document vide ou sans contenu : {metadata.get('source', 'source inconnue')}")
            return []
            
        # Si le contenu est plus petit que la taille de chunk, le retourner tel quel
        if len(content) <= self.chunk_size * 4:  # ~4 caractères par token en français
            return [{
                "content": content,
                "metadata": metadata
            }]
        
        # Sinon, utiliser LangChain pour découper intelligemment
        try:
            # Convertir en format Document de LangChain
            langchain_doc = Document(page_content=content, metadata=metadata)
            
            # Découper le document
            chunks = self.text_splitter.split_documents([langchain_doc])
            
            # Convertir les chunks LangChain en notre format
            result = []
            for i, chunk in enumerate(chunks):
                # Enrichir les métadonnées avec des informations sur le chunk
                chunk_metadata = chunk.metadata.copy()
                chunk_metadata["chunk_id"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                
                # Créer le chunk final
                result.append({
                    "content": chunk.page_content,
                    "metadata": chunk_metadata
                })
            
            logger.info(f"Document découpé en {len(result)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du découpage du document: {str(e)}")
            # Fallback: retourner le document original non découpé
            return [{
                "content": content,
                "metadata": metadata
            }]
    
    def merge_small_chunks(self, chunks: List[Dict], min_size: int = 100) -> List[Dict]:
        """
        Fusionne les chunks trop petits avec les chunks adjacents.
        
        Args:
            chunks: Liste des chunks à optimiser
            min_size: Taille minimale (en caractères) pour un chunk
            
        Returns:
            Liste de chunks optimisés
        """
        if not chunks or len(chunks) <= 1:
            return chunks
            
        result = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk.copy()
                continue
                
            # Si le chunk courant est trop petit, fusionner avec le suivant
            if len(current_chunk["content"]) < min_size:
                # Fusionner le contenu
                current_chunk["content"] += "\n" + chunk["content"]
                
                # Mettre à jour les métadonnées pour indiquer la fusion
                current_chunk["metadata"]["merged"] = True
                if "chunk_ids" not in current_chunk["metadata"]:
                    current_chunk["metadata"]["chunk_ids"] = [current_chunk["metadata"].get("chunk_id", 0)]
                current_chunk["metadata"]["chunk_ids"].append(chunk["metadata"].get("chunk_id"))
            else:
                # Ajouter le chunk courant au résultat et passer au suivant
                result.append(current_chunk)
                current_chunk = chunk.copy()
        
        # Ajouter le dernier chunk
        if current_chunk:
            result.append(current_chunk)
            
        return result
    
    def process_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Traite une liste de documents et les découpe en chunks.
        
        Args:
            documents: Liste de documents à traiter
            
        Returns:
            Liste étendue de chunks
        """
        all_chunks = []
        
        for doc in documents:
            # Prétraitement du texte pour améliorer la qualité
            doc["content"] = self._preprocess_text(doc["content"])
            
            # Découpe en chunks
            chunks = self.create_chunks(doc)
            all_chunks.extend(chunks)
            
        return all_chunks
    
    def _preprocess_text(self, text: str) -> str:
        """
        Prétraite le texte avant chunking pour améliorer la qualité.
        """
        # Supprimer les espaces et retours à la ligne multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Supprimer les caractères spéciaux inutiles
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\{\}\"\'\`\-\–\—\/\&\%\+\=\*\#\@\$\€\£]', '', text)
        
        return text.strip()
