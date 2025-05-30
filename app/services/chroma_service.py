# app/services/chroma_service.py
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings
from mistralai.client import MistralClient
import numpy as np

logger = logging.getLogger(__name__)

class CustomMistralEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, api_key: str, model_name: str = "mistral-embed"):
        self.client = MistralClient(api_key=api_key)
        self.model_name = model_name

    def __call__(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings(
                model=self.model_name,
                input=texts
            )
            # Extract embeddings and convert to list of lists
            embeddings = [data.embedding for data in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return zero vectors as fallback
            return [[0.0] * 1024] * len(texts)

class ChromaService:
    """
    Service pour l'interaction avec ChromaDB pour la recherche vectorielle.
    """
    
    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: str = "data/chroma_db"
    ):
        """
        Initialise le service ChromaDB.
        
        Args:
            collection_name: Nom de la collection ChromaDB à utiliser
            persist_directory: Répertoire où est stockée la base ChromaDB
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Vérifier si le répertoire de persistance existe
        if not os.path.exists(persist_directory):
            logger.warning(f"Le répertoire ChromaDB {persist_directory} n'existe pas. Assurez-vous d'avoir indexé des documents.")
            os.makedirs(persist_directory, exist_ok=True)
        
        # Initialiser la fonction d'embedding Mistral
        try:
            # Récupérer la clé API depuis les variables d'environnement ou la configuration
            api_key = os.getenv("MISTRAL_API_KEY") or getattr(settings, "MISTRAL_API_KEY", None)
            if not api_key:
                raise ValueError("MISTRAL_API_KEY non trouvée!")
            
            # Utiliser notre fonction d'embedding personnalisée
            self.ef = CustomMistralEmbeddingFunction(
                api_key=api_key,
                model_name="mistral-embed"
            )
            
            # Initialiser le client ChromaDB
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Obtenir la collection
            try:
                self.collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.ef
                )
                logger.info(f"✅ Collection ChromaDB '{collection_name}' chargée avec succès")
                logger.info(f"📊 Taille de la collection : {self.collection.count()} documents")
            except ValueError:
                logger.warning(f"⚠️ Collection '{collection_name}' non trouvée ! Veuillez indexer des documents.")
                # Créer une collection vide                
                self.collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.ef
                )
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de ChromaDB: {str(e)}")
            self.collection = None
            
    def search(
        self,
        query: str,
        k: int = 3,
        threshold: float = 0.35,  # Augmentation du seuil pour limiter les résultats non pertinents
        filter_criteria: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Recherche les documents similaires à une requête dans ChromaDB.
        
        Args:
            query: La requête utilisateur
            k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum (0-1)
            filter_criteria: Filtres optionnels pour la recherche
            
        Returns:
            Liste des documents pertinents avec leurs métadonnées
        """
        if not self.collection:
            logger.warning("⚠️ Aucune collection ChromaDB disponible pour la recherche!")
            return []
        
        try:
            # Effectuer la recherche dans ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=filter_criteria  # Filtrer par métadonnées si spécifié
            )
            
            # Traiter les résultats
            documents = []
            
            # Vérifier si des résultats ont été trouvés
            if not results["documents"] or not results["documents"][0]:
                logger.info("Aucun document pertinent trouvé dans ChromaDB")
                return []
            
            # Extraire les documents, scores et métadonnées
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Convertir la distance en score de similarité (1 - distance normalisée)
                # ChromaDB utilise la distance L2/cosine, donc plus la distance est faible, plus les documents sont similaires
                similarity_score = 1.0 - distance
                
                # Ne conserver que les documents au-dessus du seuil de similarité
                if similarity_score < threshold:
                    continue
                
                # Préparer les métadonnées
                source = metadata.get("source", "Document inconnu")
                page = metadata.get("page")
                
                # Ajouter à la liste des documents pertinents
                documents.append({
                    "content": doc,
                    "source": source,
                    "page": page,
                    "score": similarity_score,
                    "metadata": metadata  # Inclure toutes les métadonnées
                })
            
            logger.info(f"✅ {len(documents)} documents pertinents trouvés dans ChromaDB")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche dans ChromaDB: {str(e)}")
            return []
