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
from app.services.document_generator_service import DocumentGeneratorService  # Import du service de génération de documents
from app.models.model import Conversation, Question, Response, User
from app.db.database import SessionLocal
from mistralai.client import MistralClient
import os
from fastapi import HTTPException
import json
from datetime import datetime

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
            
        # Initialiser le service de génération de documents
        try:
            self.document_generator = DocumentGeneratorService()
            logger.info("✅ Service de génération de documents initialisé avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation du service de génération de documents: {str(e)}")
            logger.warning("⚠️ Le service de génération de documents sera désactivé")
            self.document_generator = None
            
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
        """        # Déterminer la catégorie et nettoyer les conversations expirées
        category = self._determine_category(request.query)
        self._cleanup_expired_conversations()
        
        # Récupérer l'historique ou initialiser une nouvelle conversation
        conversation_history = self.conversations.get(conversation_id) if conversation_id in self.conversations else []
        self.timestamps[conversation_id] = time.time()
        
        try:
            # Collecter tous les documents pertinents (vectoriels + contexte fourni)
            all_relevant_documents = []
            sources = []
            has_relevant_docs = False  # Variable pour suivre si des documents pertinents ont été trouvés
            
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
            # Évaluer la pertinence des documents trouvés
            relevant_docs = []
            has_relevant_docs = False
            
            # Ignorer les documents pour les questions très générales ou sans rapport avec le domaine juridique
            simple_questions = ["ca va", "ça va", "comment vas-tu", "bonjour", "salut", "hello", "coucou"]
            if any(simple_q in request.query.lower() for simple_q in simple_questions) and len(request.query) < 20:
                # Si la requête est une question très simple/générale, ne pas inclure de sources
                logger.info("Question générale détectée, pas de sources nécessaires")
                all_relevant_documents = []
            
            if all_relevant_documents:# Filtrer les documents avec un score de pertinence élevé                # Exclure complètement les questions très générales
                simple_questions = ["ca va", "ça va", "comment vas-tu", "bonjour", "salut", "hello", "coucou"]
                is_simple_question = any(simple_q in request.query.lower() for simple_q in simple_questions) and len(request.query) < 20
                
                if not is_simple_question:
                    for doc in all_relevant_documents:
                        # Considérer les documents fournis comme toujours pertinents
                        if 'score' in doc and doc['score'] > 0.7:  # Seuil encore plus élevé pour éviter les faux positifs
                            relevant_docs.append(doc)
                            has_relevant_docs = True
                        elif doc.get('source', '').startswith('Document fourni'):
                            # Les documents fournis par l'utilisateur sont toujours considérés comme pertinents
                            relevant_docs.append(doc)
                            has_relevant_docs = True
                
                if has_relevant_docs:
                    context = "Contexte juridique pertinent:\n\n"
                    sources = []  # Réinitialiser les sources pour ne garder que les pertinentes
                    
                    for i, doc in enumerate(relevant_docs, 1):
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
                    # Aucun document pertinent malgré la recherche
                    logger.info("🔍 Documents trouvés mais pas assez pertinents pour la requête")
                    context = ""
                    sources = []
                    excerpts = []
            else:
                context = ""
                sources = []
                excerpts = []

            # Génération de la réponse avec le contexte enrichi
            answer = await self._generate_response(request.query, conversation_history, context)
            
            # Mise à jour de l'historique de conversation
            conversation_history.append({"role": "user", "message": request.query})
            conversation_history.append({"role": "assistant", "message": answer})            # Limitation de la taille de l'historique
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
                    raise HTTPException(status_code=404, detail="Conversation non trouvée.")
                
                # Ajouter la question
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
                  # Vérifier si c'est le premier échange (1 question + 1 réponse)
                # et mettre à jour le titre et la catégorie intelligemment
                question_count = db.query(Question).filter(
                    Question.conversation_id == db_conversation.id
                ).count()
                
                if question_count == 1:
                    logger.info(f"Premier échange détecté pour la conversation {conversation_id}, mise à jour des métadonnées...")
                    await self.update_conversation_metadata(conversation_id, db)
            finally:
                db.close()
                
            # Détecter si l'utilisateur demande explicitement un document
            doc_detection = self._detect_document_request(request.query)
            generated_document = None
            
            # Si c'est une demande de document et que le service de génération est disponible
            if doc_detection["is_doc_request"] and hasattr(self, 'document_generator') and self.document_generator:
                try:
                    # Ouvrir une nouvelle session DB pour récupérer les informations de la conversation
                    doc_db = SessionLocal()
                    try:
                        db_conversation = doc_db.query(Conversation).filter_by(uuid=conversation_id).first()
                        if db_conversation:
                            # Déterminer le format (PDF par défaut si non spécifié)
                            doc_format = doc_detection["format"] or "pdf"
                            
                            # Générer le titre du document
                            doc_title = f"Réponse à: {request.query[:50]}" if len(request.query) > 50 else f"Réponse à: {request.query}"
                            
                            # Préparer le contenu du document
                            doc_content = f"Question: {request.query}\n\nRéponse: {answer}"
                            
                            # Générer les métadonnées
                            metadata = {
                                "Date de génération": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "ID de conversation": conversation_id,
                                "Type": "Réponse automatique"
                            }
                            
                            # Générer le document selon le format demandé
                            if doc_format.lower() == "pdf":
                                file_path = self.document_generator.generate_pdf(
                                    title=doc_title, 
                                    content=doc_content, 
                                    metadata=metadata,
                                    sources=sources if sources and has_relevant_docs else None
                                )
                            else:  # docx
                                file_path = self.document_generator.generate_word(
                                    title=doc_title, 
                                    content=doc_content, 
                                    metadata=metadata,
                                    sources=sources if sources and has_relevant_docs else None
                                )
                            
                            # Récupérer le nom du fichier
                            filename = os.path.basename(file_path)
                            
                            # Créer l'info du document généré
                            generated_document = {
                                "filename": filename,
                                "url": f"/api/document-generator/download/{filename}",
                                "format": doc_format
                            }
                            
                            # Ajouter une note à la réponse concernant le document
                            answer += f"\n\nJ'ai également généré un document {doc_format.upper()} avec cette réponse que vous pouvez télécharger."
                            
                            logger.info(f"Document {doc_format} généré automatiquement: {filename}")
                    finally:
                        doc_db.close()
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la génération automatique du document: {str(e)}")
                    answer += "\n\nDésolé, je n'ai pas pu générer le document demandé suite à une erreur technique."
            
            # Préparer la réponse avec ou sans document généré
            from app.schemas.chat import DocumentInfo
            doc_info = None
            if generated_document:
                doc_info = DocumentInfo(
                    filename=generated_document["filename"],
                    url=generated_document["url"],
                    format=generated_document["format"]
                )
            
            # Ne retourner les sources et extraits que s'ils sont pertinents
            if has_relevant_docs:
                return ChatResponse(
                    answer=answer,
                    sources=sources,
                    conversation_id=conversation_id,
                    excerpts=excerpts,
                    generated_document=doc_info
                )
            else:
                # Ne pas inclure de sources ou extraits si aucun document pertinent n'a été trouvé
                return ChatResponse(
                    answer=answer,
                    sources=[],  # Pas de sources à afficher
                    conversation_id=conversation_id,
                    excerpts=[],  # Pas d'extraits à afficher
                    generated_document=doc_info
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
1. Si un contexte juridique est fourni, utilise UNIQUEMENT ces informations pour élaborer ta réponse
2. Si le contexte ne contient pas suffisamment d'informations pour répondre à la question, indique-le clairement
3. Cite précisément tes sources (document, page, article, texte de loi, etc.) UNIQUEMENT quand tu utilises le contexte fourni
4. N'invente JAMAIS de références juridiques ou de règlements qui ne seraient pas mentionnés explicitement dans le contexte
5. Présente les informations de façon structurée avec des paragraphes courts et des puces lorsque c'est pertinent
6. Exprime-toi dans un français clair, précis et accessible, en évitant le jargon juridique complexe
7. Lorsque tu cites des extraits du contexte, indique clairement qu'il s'agit de citations
8. Si AUCUN contexte n'est fourni, réponds de manière générale sans inventer de références juridiques spécifiques

Tu dois être une aide précieuse pour les responsables de Junior-Entreprises qui ont besoin d'informations juridiques fiables."""            # Intégration optimisée du contexte RAG dans le prompt utilisateur
            if context:
                user_prompt = f"""En te basant UNIQUEMENT sur les informations juridiques suivantes:

{context}

Réponds à ma question de manière structurée et précise. N'hésite pas à citer des extraits pertinents du contexte pour appuyer ton propos.
Si les informations fournies ne sont pas suffisamment pertinentes pour répondre à ma question, indique-le clairement.

Ma question: {query}"""
            else:
                user_prompt = f"""Ma question est: {query}

Je comprends que tu n'as pas de contexte juridique spécifique pour répondre à cette question. 
Réponds de la façon la plus précise possible en fonction des connaissances générales dont tu disposes, sans citer de sources spécifiques.
Si cette question nécessite des informations juridiques spécialisées que tu ne possèdes pas, indique-le clairement."""
            
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
    
    async def generate_smart_title(self, query: str, response: str) -> dict:
        """
        Génère un titre intelligent pour la conversation basé sur la première question et réponse.
        Utilise le LLM pour créer un titre pertinent et déterminer la catégorie.
        
        Args:
            query: La première question de l'utilisateur
            response: La première réponse du système
            
        Returns:
            Un dictionnaire contenant le titre et la catégorie
        """
        try:
            # Liste des catégories disponibles
            categories = ["treasury", "organisational", "legal", "general", "other"]
            category_descriptions = {
                "treasury": "Finance, comptabilité, budget, TVA, trésorerie",
                "organisational": "Structure, organisation, management, équipe, gestion",
                "legal": "Juridique, légal, contrats, règlements",
                "general": "Questions générales sur l'entreprise",
                "other": "Autres sujets"
            }
            
            # Construction du prompt pour le LLM
            prompt = f"""Analyse la question suivante et sa réponse, puis:
1. Génère un titre concis en français (maximum 50 caractères) qui résume bien le sujet
2. Classe cette conversation dans une de ces catégories: {', '.join(categories)}

Descriptions des catégories:
- treasury: {category_descriptions["treasury"]}
- organisational: {category_descriptions["organisational"]}
- legal: {category_descriptions["legal"]}
- general: {category_descriptions["general"]}
- other: {category_descriptions["other"]}

Question: {query}

Réponse: {response}

Réponds exactement au format JSON suivant:
{{
  "title": "Titre concis",
  "category": "catégorie choisie"
}}
"""
            # Appel au LLM pour générer le titre et la catégorie
            chat_response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui analyse des conversations et génère des titres pertinents."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraire la réponse du modèle
            result_text = chat_response.choices[0].message.content
            
            try:
                # Extraire le JSON de la réponse
                import json
                import re
                
                # Chercher un objet JSON dans la réponse
                json_match = re.search(r'({[\s\S]*})', result_text)
                if json_match:
                    result_json = json.loads(json_match.group(1))
                else:
                    # Fallback si le format n'est pas respecté
                    logger.warning("Format JSON non respecté dans la réponse du LLM")
                    return {
                        "title": self._generate_title(query),  # Utiliser la méthode simple comme fallback
                        "category": self._determine_category(query)
                    }
                
                # Valider les champs requis
                if "title" not in result_json or "category" not in result_json:
                    raise ValueError("Les champs title et category sont requis dans la réponse")
                
                # Vérifier que la catégorie est valide
                if result_json["category"] not in categories:
                    result_json["category"] = "other"
                
                # Limiter la taille du titre si nécessaire
                if len(result_json["title"]) > 50:
                    result_json["title"] = result_json["title"][:47] + "..."
                
                logger.info(f"Titre généré: {result_json['title']}, Catégorie: {result_json['category']}")
                return result_json
                
            except Exception as e:
                logger.error(f"Erreur de parsing du JSON: {str(e)}")
                # En cas d'erreur, utiliser les méthodes simples comme fallback
                return {
                    "title": self._generate_title(query),
                    "category": self._determine_category(query)
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du titre intelligent: {str(e)}")
            # En cas d'erreur, utiliser les méthodes simples comme fallback
            return {
                "title": self._generate_title(query),
                "category": self._determine_category(query)
            }
    
    async def update_conversation_metadata(self, conversation_id: str, db: Session) -> bool:
        """
        Met à jour les métadonnées (titre et catégorie) d'une conversation après le premier échange.
        
        Args:
            conversation_id: L'identifiant de la conversation
            db: Session de base de données
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            # Récupérer la conversation
            conversation = db.query(Conversation).filter(Conversation.uuid == conversation_id).first()
            if not conversation:
                logger.warning(f"Conversation non trouvée pour l'ID {conversation_id}")
                return False
            
            # Récupérer la première question et la première réponse
            first_question = db.query(Question).filter(
                Question.conversation_id == conversation.id
            ).order_by(Question.created_at).first()
            
            if not first_question:
                logger.warning(f"Aucune question trouvée pour la conversation {conversation_id}")
                return False
            
            first_response = db.query(Response).filter(
                Response.question_id == first_question.id
            ).first()
            
            if not first_response:
                logger.warning(f"Aucune réponse trouvée pour la première question de la conversation {conversation_id}")
                return False
            
            # Générer un titre intelligent et une catégorie
            metadata = await self.generate_smart_title(
                query=first_question.question_text,
                response=first_response.response_text
            )
            
            # Mettre à jour la conversation
            conversation.title = metadata["title"]
            conversation.category = metadata["category"]
            conversation.updated_at = datetime.utcnow()
            
            # Enregistrer les modifications
            db.commit()
            
            logger.info(f"Métadonnées mises à jour pour la conversation {conversation_id}: {metadata}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des métadonnées: {str(e)}")
            return False
    def _detect_document_request(self, query: str) -> dict:
        """
        Détecte si la requête de l'utilisateur concerne la génération d'un document.
        
        Args:
            query: La requête de l'utilisateur
            
        Returns:
            Un dictionnaire avec les informations sur la détection :
                - is_doc_request: True si la requête concerne un document
                - format: 'pdf' ou 'docx' si spécifié, None sinon
        """
        # Normaliser la requête pour la recherche
        query_lower = query.lower().strip()
        
        # Mots clés pour détecter une demande de document (plus complets et variés)
        doc_keywords = [
            # Demandes directes
            "générer un document", "generer un document", "génère un document", "genere un document",
            "crée un document", "cree un document", "créer un document", "creer un document",
            "faire un document", "produire un document", "exporter en", "exporte en",
            "générer un pdf", "generer un pdf", "génère un pdf", "genere un pdf",
            "générer un word", "generer un word", "génère un word", "genere un word",
            
            # Formats spécifiques
            "en format", "au format", "en pdf", "en word", "document pdf", "document word",
            "fichier pdf", "fichier word", "rapport pdf", "rapport word",
            
            # Tournures variées
            "sous forme de document", "sous forme de pdf", "sous forme de word",
            "sous forme d'un document", "sous forme d'un pdf", "sous forme d'un word",
            "me donner un document", "me fournir un document", "me donner un pdf", "me fournir un pdf",
            "me donner un word", "me fournir un word", "m'envoyer un document", "m'envoyer un pdf",
            "télécharger un document", "telecharger un document", "télécharger un pdf", "telecharger un pdf",
            
            # Expressions plus complexes
            "je voudrais un document", "j'aimerais un document", "je souhaiterais un document", 
            "je voudrais un pdf", "j'aimerais un pdf", "je souhaiterais un pdf",
            "peux-tu me faire un document", "peux-tu me faire un pdf", "peux-tu me faire un word",
            "peux-tu générer un document", "peux-tu generer un document",
            "pourrais-tu me faire un document", "pourrais-tu générer un document",
            
            # Demandes spécifiques
            "version pdf", "version word", "convertir en pdf", "convertir en word",
            "réponse en pdf", "reponse en pdf", "réponse en document", "reponse en document"
        ]
        
        # Expressions plus longues et complètes
        doc_phrases = [
            "je veux ta réponse en pdf",
            "je veux ta réponse en word",
            "je veux cette réponse en pdf",
            "je veux cette réponse en word",
            "peut-on avoir cette réponse sous forme de document",
            "peut-on avoir cette réponse sous forme de pdf",
            "peut-on avoir cette réponse sous forme de word",
            "génère-moi un document avec cette réponse",
            "génère-moi un pdf avec cette réponse",
            "génère-moi un word avec cette réponse",
            "transforme ta réponse en document",
            "transforme ta réponse en pdf",
            "transforme ta réponse en word",
            "donne-moi ta réponse dans un document",
            "donne-moi ta réponse dans un pdf",
            "donne-moi ta réponse dans un word"
        ]
        
        # Vérifier si la requête contient un mot clé de document ou une phrase complète
        is_doc_request = any(keyword in query_lower for keyword in doc_keywords) or \
                        any(phrase in query_lower for phrase in doc_phrases)
        
        # Vérifier les expressions de début ou fin de phrase
        doc_starts = [
            "document", "pdf", "word", "docx", 
            "faire un", "générer un", "generer un", "créer un", "creer un"
        ]
        
        if not is_doc_request:
            # Vérifier si la requête commence ou se termine par certains mots clés
            is_doc_request = query_lower.startswith(tuple(doc_starts)) or \
                            query_lower.endswith(("en pdf", "en word", "en document", "en docx", "en doc"))
        
        # Analyse avancée: rechercher des structures de phrases typiques
        if not is_doc_request:
            import re
            # Patterns comme "... en format pdf", "... sous forme de document", etc.
            doc_patterns = [
                r"en\s+(?:format|forme(?:\s+de)?)(?:\s+de)?\s+(?:document|pdf|word|docx|doc)",
                r"sous\s+(?:format|forme)(?:\s+d[e'](?:un)?)?\s+(?:document|pdf|word|docx|doc)",
                r"(?:générer|generer|créer|creer|produire|faire)(?:\s+un)?\s+(?:document|pdf|word|docx|doc)"
            ]
            
            is_doc_request = any(re.search(pattern, query_lower) for pattern in doc_patterns)
        
        # Déterminer le format demandé
        format_type = None
        
        # Priorité aux formats explicitement mentionnés
        if "pdf" in query_lower:
            format_type = "pdf"
        elif any(word in query_lower for word in ["word", "docx", "doc"]):
            format_type = "docx"
            
        # Si aucun format spécifique n'est mentionné mais c'est une demande de document,
        # utiliser PDF comme format par défaut
        if is_doc_request and not format_type:
            format_type = "pdf"  # Format par défaut
        
        return {
            "is_doc_request": is_doc_request,
            "format": format_type
        }
