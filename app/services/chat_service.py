from typing import Dict, List, Optional
import uuid
import time
import logging
from collections import OrderedDict
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.models.model import Conversation, Question, Response, User
from app.db.database import SessionLocal
from mistralai import Mistral
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
    # Dans la méthode __init__ de la classe ChatService
    def __init__(self, 
             model_name: str = "mistral-large-latest", 
             max_conversations: int = 1000,
             conversation_ttl: int = 3600):
        self.retrieval_service = RetrievalService()
        self.embedding_service = EmbeddingService()
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
            
            self.client = Mistral(api_key=mistral_api_key)
            self.model = model_name
            if os.path.exists(self.embedding_service.index_path):
                self.embedding_service.load_index()
            logger.info("Client Mistral API (v1) initialisé avec base vectorielle chargée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Mistral: {str(e)}")
            raise

    async def process_query(self, request: ChatRequest, conversation_id: str, user_id: int) -> ChatResponse:
        """
        Traite une requête utilisateur et génère une réponse.
        """
        category = "other"  # Valeur par défaut
        self._cleanup_expired_conversations()
        conversation_history = self.conversations.get(conversation_id) if conversation_id in self.conversations else []
        self.timestamps[conversation_id] = time.time()

        try:
            # 🔍 Étape RAG : recherche de documents similaires
            relevant_documents = self.embedding_service.search(request.query, k=3)
            context = ""
            if relevant_documents:
                context = "Contexte juridique pertinent:\n"
                for i, doc in enumerate(relevant_documents, 1):
                    context += f"{i}. {doc['content'][:500]}... (Source: {doc['source']})\n"

            answer = await self._generate_response(request.query, conversation_history, context)
            sources = [doc['source'] for doc in relevant_documents] if relevant_documents else []

            conversation_history.append({"role": "user", "message": request.query})
            conversation_history.append({"role": "assistant", "message": answer})

            if len(conversation_history) > self.max_history_messages * 2:
                conversation_history = conversation_history[-self.max_history_messages * 2:]

            self.conversations.put(conversation_id, conversation_history)

            # 💾 Enregistrer en base de données
            db: Session = SessionLocal()
            try:
                # Récupérer la conversation existante
                db_conversation = db.query(Conversation).filter_by(uuid=conversation_id).first()
                if not db_conversation:
                    logger.error(f"Conversation non trouvée pour conversation_id={conversation_id}")

                    raise HTTPException(status_code=404, detail="Conversation non trouvée.")

                # Ajouter la question
                db_question = Question(question_text=request.query, conversation_id=db_conversation.id)
                db.add(db_question)
                db.commit()
                db.refresh(db_question)

                # Ajouter la réponse
                db_response = Response(
                    response_text=answer,
                    conversation_id=db_conversation.id,
                    question_id=db_question.id
                )
                db.add(db_response)
                db.commit()
            finally:
                db.close()

            return ChatResponse(
                answer=answer,
                sources=sources,
                conversation_id=conversation_id
            )

        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête: {str(e)}", exc_info=True)
            return ChatResponse(
                answer="Je suis désolé, une erreur s'est produite lors du traitement de votre demande.",
                sources=[],
                conversation_id=conversation_id
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
        try:
            history_messages = [
                {"role": msg["role"], "content": msg["message"]}
                for msg in conversation_history[-6:]
            ]

            prompt = f"{context}\nQuestion: {query}" if context else query

            chat_response = await self.client.chat.complete_async(
                model=self.model,
                messages=[*history_messages, {"role": "user", "content": prompt}]
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
        Récupère l'historique complet d'une conversation à partir de son ID.
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
            # Ajustez ceci selon votre modèle de données réel
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
                    history.append({
                        "role": "assistant",
                        "content": response.response_text,
                        "timestamp": response.created_at.isoformat() if hasattr(response, 'created_at') else None
                    })
            
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
