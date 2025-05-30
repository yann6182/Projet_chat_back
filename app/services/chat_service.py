from typing import Dict, List, Optional
import uuid
import time
import logging
from collections import OrderedDict
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse, Excerpt
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService  # Import du nouveau service ChromaDB
from app.models.model import Conversation, Question, Response, User
from app.db.database import SessionLocal
from mistralai.client import MistralClient
import os
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def __contains__(self, key):
        return key in self.cache

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            return True
        return False

class ChatService:
    def __init__(self, 
                 model_name: str = "mistral-large-latest", 
                 max_conversations: int = 1000,
                 conversation_ttl: int = 3600):
        self.retrieval_service = RetrievalService()
        
        # Initialisation des services d'embedding et de recherche vectorielle
        try:
            self.embedding_service = EmbeddingService()
            # Initialiser également le service ChromaDB
            self.chroma_service = ChromaService()
            self.use_chroma = True  # Utiliser ChromaDB par défaut si disponible
            logger.info("✅ Services d'embedding et ChromaDB initialisés avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation des services RAG: {str(e)}")
            logger.warning("⚠️ Le service RAG sera désactivé")
            self.embedding_service = None
            self.chroma_service = None
            self.use_chroma = False
            
        self.conversations = LRUCache(max_conversations)
        self.timestamps = {}
        self.conversation_ttl = conversation_ttl
        self.max_history_messages = 5
        self.max_output_tokens = 200

        try:
            # Utiliser directement le chemin absolu vers le fichier .env
            from dotenv import load_dotenv
            import os
            
            # Chargement explicite du fichier .env
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', '.env')
            load_dotenv(env_path)
            
            # Récupérer la clé API après chargement
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                logger.error(f"Clé API Mistral non trouvée dans {env_path}")
                raise ValueError("Clé API Mistral non trouvée")
            
            # Afficher la clé partiellement pour debug (premiers et derniers caractères)
            key_preview = mistral_api_key[:4] + "..." + mistral_api_key[-4:]
            logger.info(f"Clé API Mistral trouvée: {key_preview}")
            
            self.client = MistralClient(api_key=mistral_api_key)
            self.model = model_name
            if os.path.exists(self.embedding_service.index_path):
                self.embedding_service.load_index()
            logger.info("Client Mistral API (v1) initialisé avec base vectorielle chargée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Mistral: {str(e)}")
            raise
            
    def _generate_title(self, query: str) -> str:
        """
        Génère un titre pour la conversation basé sur la requête initiale.
        """
        max_length = 50  # Limite de caractères pour le titre
        title = query.strip().capitalize()
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + "..."
        return title
        
    async def process_query(self, request: ChatRequest, conversation_id: str, user_id: int) -> ChatResponse:
        """
        Traite une requête utilisateur et génère une réponse en utilisant l'architecture RAG.
        
        Args:
            request: La requête utilisateur
            conversation_id: L'identifiant de la conversation
            user_id: L'identifiant de l'utilisateur
            
        Returns:
            La réponse structurée avec contexte et sources
        """
        # Déterminer la catégorie et nettoyer les conversations expirées
        category = self._determine_category(request.query)
        self._cleanup_expired_conversations()
        
        # Récupérer l'historique ou initialiser une nouvelle conversation
        conversation_history = self.conversations.get(conversation_id) if conversation_id in self.conversations else []
        self.timestamps[conversation_id] = time.time()
        try:
            # Collecter tous les documents pertinents (vectoriels + contexte fourni)
            all_relevant_documents = []
            sources = []
            
            # 1. Ajouter les documents contextuels fournis par le front-end, s'il y en a
            if hasattr(request, 'context_documents') and request.context_documents:
                logger.info(f"Documents contextuels fournis par le front-end: {len(request.context_documents)}")
                for i, doc in enumerate(request.context_documents):
                    # Convertir en dictionnaire pour le format compatible avec les autres documents
                    all_relevant_documents.append({
                        'content': doc.content,
                        'source': f"Document fourni: {doc.source}",
                        'page': doc.page,
                        'score': 0.0  # Score artificiel pour prioriser ces documents
                    })
                    sources.append(f"Document fourni: {doc.source}")
              # 2. 🔍 Étape RAG : recherche de documents similaires dans la base vectorielle
            # Utiliser ChromaDB si disponible, sinon fallback sur l'ancien service d'embedding
            if self.use_chroma and hasattr(self, 'chroma_service') and self.chroma_service:
                try:
                    logger.info("🔍 Recherche de documents similaires dans ChromaDB")
                    vector_documents = self.chroma_service.search(
                        query=request.query, 
                        k=3,  # Récupérer les 3 documents les plus pertinents
                        threshold=0.25  # Filtrer les documents peu pertinents
                    )
                    # Ajouter les documents de ChromaDB
                    all_relevant_documents.extend(vector_documents)
                    
                    # Ajouter les sources
                    for doc in vector_documents:
                        source_info = doc['source']
                        if doc.get('page'):
                            source_info += f" (page {doc['page']})"
                        if source_info not in sources:
                            sources.append(source_info)
                    
                    logger.info(f"✅ {len(vector_documents)} documents pertinents trouvés dans ChromaDB")
                            
                except Exception as e:
                    logger.warning(f"❌ Impossible d'effectuer la recherche ChromaDB: {str(e)}")
                    # Fallback sur l'ancien service d'embedding si disponible
                    if hasattr(self, 'embedding_service') and self.embedding_service:
                        try:
                            logger.info("🔄 Utilisation du service d'embedding de secours (FAISS)")
                            vector_documents = self.embedding_service.search(
                                query=request.query, 
                                k=3,
                                threshold=0.25
                            )
                            all_relevant_documents.extend(vector_documents)
                            
                            # Ajouter les sources
                            for doc in vector_documents:
                                source_info = doc['source']
                                if doc.get('page'):
                                    source_info += f" (page {doc['page']})"
                                if source_info not in sources:
                                    sources.append(source_info)
                        except Exception as e:
                            logger.warning(f"❌ Impossible d'effectuer la recherche RAG avec FAISS: {str(e)}")
            elif hasattr(self, 'embedding_service') and self.embedding_service:
                # Utiliser l'ancien service d'embedding si ChromaDB n'est pas disponible
                try:
                    logger.info("🔄 Utilisation du service d'embedding FAISS")
                    vector_documents = self.embedding_service.search(
                        query=request.query, 
                        k=3,  # Récupérer les 3 documents les plus pertinents
                        threshold=0.25  # Filtrer les documents peu pertinents
                    )
                    # Ajouter les documents de la base vectorielle
                    all_relevant_documents.extend(vector_documents)
                    
                    # Ajouter les sources
                    for doc in vector_documents:
                        source_info = doc['source']
                        if doc.get('page'):
                            source_info += f" (page {doc['page']})"
                        if source_info not in sources:
                            sources.append(source_info)
                            
                except Exception as e:
                    logger.warning(f"❌ Impossible d'effectuer la recherche RAG: {str(e)}")
              # 3. 🔍 Étape ChromaDB : recherche de documents similaires dans ChromaDB, si activé
            if self.use_chroma and hasattr(self, 'chroma_service'):
                try:
                    chroma_documents = self.chroma_service.search(
                        query=request.query,
                        k=3,  # Récupérer les 3 documents les plus pertinents
                        filter_criteria=None  # Aucun filtre supplémentaire pour l'instant
                    )
                    
                    logger.info(f"Documents trouvés dans ChromaDB: {len(chroma_documents)}")
                    
                    # Ajouter les documents de ChromaDB
                    all_relevant_documents.extend(chroma_documents)
                    
                    # Ajouter les sources
                    for doc in chroma_documents:
                        source_info = doc['source']
                        if doc.get('page'):
                            source_info += f" (page {doc['page']})"
                        if source_info not in sources:
                            sources.append(source_info)
                            
                except Exception as e:
                    logger.warning(f"Impossible d'effectuer la recherche dans ChromaDB: {str(e)}")
              
            # Enrichissement du contexte avec tous les documents pertinents
            context = ""
            # Préparer la liste des extraits utilisés pour la réponse
            excerpts = []
            if all_relevant_documents:
                context = "Contexte juridique pertinent:\n\n"
                for i, doc in enumerate(all_relevant_documents, 1):
                    # Limiter la taille des extraits pour éviter de dépasser le contexte
                    excerpt = doc['content']
                    if len(excerpt) > 800:  # Limiter à 800 caractères par extrait
                        excerpt = excerpt[:800] + "..."

                    # Inclure la source et le numéro de page si disponible
                    source_info = doc['source']
                    page = doc.get('page')
                    if page:
                        source_info += f" (page {page})"

                    # Ajouter l'extrait au contexte
                    context += f"Document {i}: {excerpt}\nSource: {source_info}\n\n"

                    # Collecter les sources pour la réponse
                    if source_info not in sources:
                        sources.append(source_info)

                    # Ajouter à la liste des extraits pour l'API
                    excerpts.append({
                        "content": excerpt,
                        "source": doc['source'],
                        "page": doc.get('page')
                    })
            else:
                context = ""
                excerpts = []

            # Génération de la réponse avec le contexte enrichi
            answer = await self._generate_response(request.query, conversation_history, context)
            
            # Mise à jour de l'historique de conversation
            conversation_history.append({"role": "user", "message": request.query})
            conversation_history.append({"role": "assistant", "message": answer})

            # Limitation de la taille de l'historique
            if len(conversation_history) > self.max_history_messages * 2:
                conversation_history = conversation_history[-self.max_history_messages * 2:]

            # Mise en cache de la conversation
            self.conversations.put(conversation_id, conversation_history)

            # 💾 Enregistrer en base de données
            db: Session = SessionLocal()
            try:
                # Récupérer la conversation existante
                db_conversation = db.query(Conversation).filter_by(uuid=conversation_id).first()
                if not db_conversation:
                    logger.error(f"Conversation non trouvée pour conversation_id={conversation_id}")

                    raise HTTPException(status_code=404, detail="Conversation non trouvée.")                # Ajouter la question
                db_question = Question(question_text=request.query, conversation_id=db_conversation.id)
                db.add(db_question)
                db.commit()
                db.refresh(db_question)
                
                # Ajouter la réponse avec les données RAG (sources et extraits)
                db_response = Response(
                    response_text=answer,
                    conversation_id=db_conversation.id,
                    question_id=db_question.id,
                    sources=sources if sources else None,  # Liste des sources
                    excerpts=excerpts if excerpts else None  # Les extraits sont déjà au format dict
                )
                db.add(db_response)
                db.commit()
            finally:
                db.close()

            return ChatResponse(
                answer=answer,
                sources=sources,
                conversation_id=conversation_id,
                excerpts=excerpts
            )

        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête: {str(e)}", exc_info=True)
            # Toujours retourner une chaîne pour conversation_id (jamais None)
            safe_conversation_id = conversation_id if conversation_id else ""
            return ChatResponse(
                answer="Je suis désolé, une erreur s'est produite lors du traitement de votre demande.",
                sources=[],
                conversation_id=safe_conversation_id
            )
            
    def _determine_category(self, query: str) -> str:
        """
        Détermine la catégorie de la question basée sur des mots-clés.
        """
        query = query.lower()
        
        # Définition des catégories et mots-clés associés
        category_keywords = {
            'treasury': ['trésorerie', 'finance', 'budget', 'financial', 'comptable', 'accounting', 'tva'],
            'organisational': ['structure', 'organisation', 'management', 'réunion', 'équipe', 'team', 'gestion'],
            'other': ['juridique', 'legal', 'général', 'question', 'help', 'aide']
        }
        
        # Vérifier les mots-clés dans la requête
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return category
                    
        return "other"  # Catégorie par défaut
    async def _generate_response(self, query: str, conversation_history: List[Dict], context: str = "") -> str:
        """
        Génère une réponse basée sur la requête, l'historique et le contexte RAG.
        Utilise une structure de prompt optimisée pour maximiser la pertinence du contexte juridique.
        
        Args:
            query: La question de l'utilisateur
            conversation_history: L'historique de la conversation
            context: Le contexte extrait de la base de connaissances (documents pertinents)
            
        Returns:
            La réponse générée par le modèle
        """
        try:
            # Préparer l'historique de conversation au format attendu par l'API
            history_messages = []
            
            # Ne garder que les 6 derniers messages pour éviter de dépasser le contexte
            for msg in conversation_history[-6:]:
                # Conversion du format interne au format API
                history_messages.append({
                    "role": msg["role"], 
                    "content": msg.get("message", msg.get("content", ""))
                })
            
            # Construction du système prompt optimisé pour le contexte juridique des Junior-Entreprises
            system_prompt = """Tu es un assistant juridique spécialisé pour les Junior-Entreprises en France.
Tu fais preuve de précision, de clarté et de pédagogie dans tes réponses.

DIRECTIVES IMPORTANTES:
1. Utilise UNIQUEMENT les informations fournies dans le contexte pour élaborer ta réponse
2. Si le contexte ne contient pas suffisamment d'informations pour répondre à la question, indique-le clairement
3. Cite précisément tes sources (document, page, article, texte de loi, etc.)
4. N'invente JAMAIS de références juridiques ou de règlements qui ne seraient pas mentionnés explicitement dans le contexte
5. Présente les informations de façon structurée avec des paragraphes courts et des puces lorsque c'est pertinent
6. Exprime-toi dans un français clair, précis et accessible, en évitant le jargon juridique complexe
7. Lorsque tu cites des extraits du contexte, indique clairement qu'il s'agit de citations

Tu dois être une aide précieuse pour les responsables de Junior-Entreprises qui ont besoin d'informations juridiques fiables."""

            # Intégration optimisée du contexte RAG dans le prompt utilisateur
            if context:
                user_prompt = f"""En te basant UNIQUEMENT sur les informations juridiques suivantes:

{context}

Réponds à ma question de manière structurée et précise. N'hésite pas à citer des extraits pertinents du contexte pour appuyer ton propos.

Ma question: {query}"""
            else:
                user_prompt = f"Ma question est: {query}\n\nRéponds de la façon la plus précise possible en fonction des informations dont tu disposes, et indique clairement si tu manques d'informations juridiques spécifiques pour répondre."
            
            # Appel à l'API Mistral avec le prompt structuré
            chat_response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *history_messages,
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return chat_response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse avec Mistral API: {str(e)}", exc_info=True)
            return "Je suis désolé, je ne peux pas générer de réponse pour le moment."
            
    def _cleanup_expired_conversations(self):
        current_time = time.time()
        expired_ids = [
            conv_id for conv_id, timestamp in self.timestamps.items()
            if current_time - timestamp > self.conversation_ttl
        ]
        for conv_id in expired_ids:
            self.clear_conversation(conv_id)
            if conv_id in self.timestamps:
                del self.timestamps[conv_id]
                
    def get_conversation_history(self, conversation_id: str) -> List[dict]:
        """
        Récupère l'historique complet d'une conversation à partir de son ID,
        y compris les données RAG (sources et extraits).
        """
        if not conversation_id:
            return []
        
        # Log pour le débogage
        print(f"Récupération de l'historique pour conversation_id: {conversation_id}")
        
        db = SessionLocal()
        try:
            # Vérifier si la conversation existe
            conversation = db.query(Conversation).filter(Conversation.uuid == conversation_id).first()
            if not conversation:
                print(f"Conversation {conversation_id} non trouvée en base")
                return []
                
            # Récupérer les questions et réponses liées à cette conversation
            from app.models.model import Question, Response
            
            # Récupérer toutes les questions pour cette conversation
            questions = db.query(Question).filter(
                Question.conversation_id == conversation.id
            ).order_by(Question.created_at).all()
            
            history = []
            
            for question in questions:
                # Récupérer la réponse associée à cette question
                response = db.query(Response).filter(
                    Response.question_id == question.id
                ).first()
                
                history.append({
                    "role": "user",
                    "content": question.question_text,
                    "timestamp": question.created_at.isoformat() if hasattr(question, 'created_at') else None
                })
                
                if response:
                    # Inclure les données RAG si disponibles
                    response_data = {
                        "role": "assistant",
                        "content": response.response_text,
                        "timestamp": response.created_at.isoformat() if hasattr(response, 'created_at') else None
                    }
                    
                    # Ajouter les sources si disponibles
                    if hasattr(response, 'sources') and response.sources:
                        response_data["sources"] = response.sources
                    
                    # Ajouter les extraits si disponibles
                    if hasattr(response, 'excerpts') and response.excerpts:
                        response_data["excerpts"] = response.excerpts
                    
                    history.append(response_data)
            
            print(f"Historique récupéré: {len(history)} messages")
            return history
            
        except Exception as e:
            print(f"Erreur lors de la récupération de l'historique: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()

    def clear_conversation(self, conversation_id: str) -> bool:
        success = self.conversations.delete(conversation_id)
        if conversation_id in self.timestamps:
            del self.timestamps[conversation_id]
        return success
