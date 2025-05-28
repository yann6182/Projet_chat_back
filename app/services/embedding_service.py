import os
import faiss
import numpy as np
from typing import List, Dict
import pickle
from mistralai.client import MistralClient
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "mistral-embed", index_path: str = "./vector_store/index.faiss", embedding_dim: int = 1024):
        """
        Initialise le service d'embedding avec le modèle Mistral.
        
        Args:
            model_name: Le nom du modèle d'embedding à utiliser (par défaut: mistral-embed)
            index_path: Chemin où stocker l'index FAISS
            embedding_dim: Dimension des embeddings (1024 pour Mistral Embed)
        """        # Charger la clé API Mistral
        from dotenv import load_dotenv
        from app.core.config import settings
        load_dotenv()
        
        # Essayer d'abord la variable d'environnement puis le fichier de configuration
        api_key = os.getenv("MISTRAL_API_KEY") or getattr(settings, "MISTRAL_API_KEY", None)
        
        if not api_key:
            logger.warning("⚠️ MISTRAL_API_KEY non trouvée! Le service d'embedding ne fonctionnera pas.")
            self.client = None
        else:
            logger.info("✅ Clé API Mistral trouvée.")
            self.client = MistralClient(api_key=api_key)
            
        self.model_name = model_name
        self.index_path = index_path
        self.embedding_dim = embedding_dim
          # Créer un index FAISS de similarité cosinus (L2 normalisé)
        self.index = faiss.IndexFlatL2(embedding_dim)  # 1024 = dimension pour mistral-embed
        self.meta_data: List[Dict] = []  # Pour stocker les infos (texte, source...)
        
        logger.info(f"Service d'embedding Mistral initialisé avec modèle {model_name}")
        
    def embed_text(self, text: str) -> np.ndarray:
        """
        Génère un embedding pour un texte donné en utilisant l'API Mistral.
        
        Args:
            text: Le texte à encoder
            
        Returns:
            Un vecteur embedding numpy ou un vecteur aléatoire si le client n'est pas disponible
        """
        # Vérifier si le client est disponible
        if not self.client:
            logger.warning("Client Mistral non disponible. Retournant un vecteur aléatoire pour le test.")
            # Générer un vecteur aléatoire pour le test - ne pas utiliser en production
            random_vec = np.random.rand(1, self.embedding_dim).astype(np.float32)
            faiss.normalize_L2(random_vec)
            return random_vec
            
        try:
            response = self.client.embeddings(
                model=self.model_name,
                input=[text]
            )
            # Extraire le vecteur d'embedding
            embedding = response.data[0].embedding
            # Convertir en numpy array et normaliser
            embedding_array = np.array([embedding], dtype=np.float32)
            # Normaliser pour la similarité cosinus
            faiss.normalize_L2(embedding_array)
            return embedding_array
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'embedding: {str(e)}")            # Retourner un vecteur aléatoire en cas d'erreur
            random_vec = np.random.rand(1, self.embedding_dim).astype(np.float32)
            faiss.normalize_L2(random_vec)
            return random_vec
            
    def build_index(self, documents: List[Dict]):
        """
        Construit un index de recherche à partir d'une liste de documents.
        
        Args:
            documents: Liste de dictionnaires contenant au moins 'content' et 'source'
        """
        if not documents:
            logger.warning("Aucun document fourni pour l'indexation")
            return
            
        # Si le client n'est pas disponible, créer un index factice pour le développement
        if not self.client:
            logger.warning("⚠️ Client Mistral non disponible. Création d'un index factice pour le développement.")
            # Créer des vecteurs aléatoires pour chaque document
            embeddings = np.random.rand(len(documents), self.embedding_dim).astype(np.float32)
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            self.meta_data = documents
            
            # Sauvegarder l'index et les métadonnées
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            with open(self.index_path.replace(".faiss", "_meta.pkl"), "wb") as f:
                pickle.dump(self.meta_data, f)
                
            logger.info(f"✅ Index factice construit avec {len(self.meta_data)} documents pour le développement.")
            return
            
        # Traiter les documents par lots pour éviter les limites d'API
        batch_size = 5  # Ajuster selon les limites de l'API
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        all_embeddings = []
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(documents))
            batch_docs = documents[start_idx:end_idx]
            
            # Extraire les textes des documents
            texts = [doc["content"] for doc in batch_docs]
            
            # Obtenir les embeddings par lot
            try:
                response = self.client.embeddings(
                    model=self.model_name,
                    input=texts
                )
                
                # Extraire les embeddings
                embeddings = [data.embedding for data in response.data]
                embeddings_array = np.array(embeddings, dtype=np.float32)
                
                # Normaliser pour la similarité cosinus
                faiss.normalize_L2(embeddings_array)
                
                all_embeddings.append(embeddings_array)
                self.meta_data.extend(batch_docs)
                
                logger.info(f"Traité le lot {i+1}/{total_batches} ({len(batch_docs)} documents)")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'indexation du lot {i+1}: {str(e)}")
        
        # Combiner tous les embeddings
        if all_embeddings:
            combined_embeddings = np.vstack(all_embeddings)
            
            # Ajouter à l'index FAISS
            self.index.add(combined_embeddings)
            
            # Sauvegarder l'index et les métadonnées
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            with open(self.index_path.replace(".faiss", "_meta.pkl"), "wb") as f:
                pickle.dump(self.meta_data, f)
            
            logger.info(f"✅ Index construit avec {len(self.meta_data)} documents.")
        else:
            logger.warning("Aucun embedding généré pour l'indexation")
    
    def load_index(self):
        """
        Charge un index FAISS existant depuis le disque.
        """
        if not os.path.exists(self.index_path):
            logger.warning("⚠️ Aucun index FAISS trouvé. Veuillez indexer des documents en premier.")
            return
    
        self.index = faiss.read_index(self.index_path)
        with open(self.index_path.replace(".faiss", "_meta.pkl"), "rb") as f:
            self.meta_data = pickle.load(f)
                
        logger.info(f"Index FAISS chargé avec {len(self.meta_data)} documents.")
    
    def search(self, query: str, k: int = 3, threshold: float = 0.25) -> List[Dict]:
        """
        Recherche les documents les plus similaires à une requête avec filtrage par seuil
        de pertinence et dédoublonnage intelligent basé sur les sources.
        
        Args:
            query: La requête utilisateur
            k: Nombre maximum de résultats à retourner
            threshold: Seuil de similarité minimum (plus la valeur est basse, plus le score est bon)
            
        Returns:
            Liste des documents les plus pertinents, triés par pertinence
        """
        if not self.meta_data or self.index.ntotal == 0:
            logger.warning("Index vide ou non initialisé")
            return []

        try:
            # Récupérer plus de résultats pour ensuite filtrer plus intelligemment
            k_search = min(k * 3, self.index.ntotal)  # Chercher 3x plus pour filtrage
            
            # Obtenir l'embedding de la requête
            query_vec = self.embed_text(query)
            
            # Rechercher dans l'index
            D, I = self.index.search(query_vec, k_search)
            
            if len(I[0]) == 0 or I[0][0] == -1:
                logger.info(f"Aucun résultat pour la requête: {query}")
                return []
                
            # Récupérer et filtrer les métadonnées correspondantes
            results = []
            seen_sources = set()  # Pour dédoublonner les sources
            
            for idx, score in zip(I[0], D[0]):
                # Vérifier le seuil de similarité (distance L2 normalisée)
                if score > threshold:
                    logger.debug(f"Document rejeté: score {score} > seuil {threshold}")
                    continue
                    
                if idx < len(self.meta_data):
                    doc = self.meta_data[idx].copy()
                    doc["score"] = float(score)  # Ajouter le score de similarité
                    
                    # Dédoublonnage intelligent par source
                    source_key = f"{doc['source']}"
                    if doc.get('page'):
                        source_key += f"_{doc['page']}"
                    
                    # Ne pas ajouter plus de 2 extraits de la même source
                    if source_key in seen_sources:
                        continue
                        
                    seen_sources.add(source_key)
                    results.append(doc)
                    
                    # Arrêter si on a atteint le nombre demandé
                    if len(results) >= k:
                        break
                    
            # Log des résultats trouvés
            if results:
                logger.info(f"Trouvé {len(results)} documents pertinents pour '{query}'")
                for i, doc in enumerate(results):
                    logger.debug(f"Document {i+1}: {doc['source']} (score: {doc['score']:.4f})")
            else:
                logger.info(f"Aucun document pertinent pour '{query}'")
                    
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return []


# Exemple d'utilisation
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
