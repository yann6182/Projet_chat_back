# Guide des modèles et services RAG

Ce document détaille la configuration et l'utilisation des modèles d'intelligence artificielle et des services RAG (Retrieval Augmented Generation) dans l'API Juridica.

## Configuration des modèles Mistral AI

L'application utilise Mistral AI pour deux fonctionnalités principales :
1. La génération de réponses aux questions des utilisateurs
2. La génération intelligente de titres et de catégories pour les conversations

### Choix du modèle

La classe `ChatService` est configurée par défaut pour utiliser le modèle `mistral-large-latest`. Vous pouvez modifier ce paramètre dans le fichier `app/services/chat_service.py` :

```python
def __init__(self, 
             model_name: str = "mistral-large-latest",  # Modèle par défaut
             max_conversations: int = 1000,
             conversation_ttl: int = 3600):
    # ...
```

Modèles disponibles :
- `mistral-large-latest` (recommandé pour les meilleures performances)
- `mistral-medium` (bon compromis performance/coût)
- `mistral-small` (plus rapide, moins précis)

Le choix du modèle affecte à la fois la qualité des réponses et la précision de la génération des titres et catégories.

## Fonctionnalité de génération automatique des titres

La nouvelle fonctionnalité de génération automatique des titres et des catégories s'active automatiquement après le premier échange dans une conversation. Voici comment elle fonctionne :

1. Après réception de la première question et génération de la première réponse
2. Le système détecte qu'il s'agit du premier échange (`question_count == 1`)
3. La méthode `update_conversation_metadata()` est appelée avec l'ID de conversation et la session DB
4. La méthode `generate_smart_title()` analyse la question et la réponse pour générer un titre pertinent et déterminer une catégorie
5. Les métadonnées de la conversation sont mises à jour en base de données

### Personnalisation des catégories

Les catégories disponibles sont définies dans la méthode `generate_smart_title()`. Vous pouvez les modifier en éditant cette méthode dans `app/services/chat_service.py` :

```python
# Liste des catégories disponibles
categories = ["treasury", "organisational", "legal", "general", "other"]
category_descriptions = {
    "treasury": "Finance, comptabilité, budget, TVA, trésorerie",
    "organisational": "Structure, organisation, management, équipe, gestion",
    "legal": "Juridique, légal, contrats, règlements",
    "general": "Questions générales sur l'entreprise",
    "other": "Autres sujets"
}
```

## Services RAG (Retrieval Augmented Generation)

L'API Juridica utilise deux technologies pour la recherche vectorielle :

1. **ChromaDB** (principal) : Une base de données vectorielle moderne optimisée pour la similarité sémantique
2. **FAISS** (fallback) : Une bibliothèque de recherche de similarité vectorielle développée par Facebook AI

Le système est configuré pour utiliser ChromaDB par défaut, avec FAISS comme solution de secours en cas de problème.

### Configuration des services d'embedding

Les services d'embedding et de recherche vectorielle sont initialisés dans le constructeur de `ChatService` :

```python
try:
    self.embedding_service = EmbeddingService()
    self.chroma_service = ChromaService()
    self.use_chroma = True  # Utiliser ChromaDB par défaut
    logger.info("✅ Services d'embedding et ChromaDB initialisés avec succès")
except Exception as e:
    logger.error(f"❌ Erreur lors de l'initialisation des services RAG: {str(e)}")
    logger.warning("⚠️ Le service RAG sera désactivé")
    self.embedding_service = None
    self.chroma_service = None
    self.use_chroma = False
```

### Gestion des documents

Les documents de la base de connaissances sont stockés dans le dossier `data/legal_docs/` et sont traités par le script d'indexation qui :

1. Extrait le texte des documents (PDF, DOCX, etc.)
2. Découpe le texte en chunks de taille appropriée
3. Génère des embeddings pour chaque chunk
4. Stocke ces embeddings dans ChromaDB et/ou FAISS

### Personnalisation des seuils de pertinence

Le seuil de pertinence des documents peut être ajusté dans la méthode `process_query()` :

```python
vector_documents = self.chroma_service.search(
    query=request.query, 
    k=3,  # Nombre de documents à récupérer
    threshold=0.25  # Seuil de similarité (0-1)
)
```

Pour des réponses plus précises mais potentiellement moins complètes, augmentez le seuil (par exemple à 0.4 ou 0.5).

## Optimisation des performances

### Mise en cache des conversations

L'application utilise un système de cache LRU (Least Recently Used) pour stocker les conversations récentes en mémoire :

```python
self.conversations = LRUCache(max_conversations)
```

Le paramètre `max_conversations` détermine combien de conversations peuvent être stockées simultanément. Augmentez cette valeur sur les serveurs disposant de plus de RAM.

### Durée de vie des conversations

Le paramètre `conversation_ttl` (Time To Live) détermine combien de temps (en secondes) une conversation reste en cache sans activité avant d'être supprimée :

```python
self.conversation_ttl = 3600  # 1 heure par défaut
```

### Limitation de l'historique

Pour optimiser les performances et éviter de dépasser les limites de contexte du modèle, l'historique des conversations est limité :

```python
self.max_history_messages = 5  # Nombre de messages conservés dans l'historique
```

Augmenter cette valeur permet d'avoir des conversations plus cohérentes sur une plus longue période, mais augmente également la consommation de tokens et donc le coût d'utilisation.
