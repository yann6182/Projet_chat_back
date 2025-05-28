# README pour l'architecture RAG du chatbot juridique

## Architecture RAG pour Junior-Entreprises

Ce guide explique comment utiliser et maintenir l'architecture RAG (Retrieval-Augmented Generation) implémentée pour le chatbot juridique des Junior-Entreprises.

### 1. Vue d'ensemble de l'architecture

L'architecture RAG implémentée combine :
- **ChromaDB** comme base de données vectorielle
- **Mistral AI** pour les embeddings et la génération de texte
- **FastAPI** comme backend avec PostgreSQL pour la persistance
- **React** pour le frontend

### 2. Indexation des documents

Pour indexer de nouveaux documents dans la base de connaissances :

```bash
# Installation des dépendances
pip install -r requirements-rag.txt

# Indexation des documents (remplacer /chemin/vers/documents par votre chemin)
python scripts/reindex_chromadb.py --docs-dir data/legal_docs --force-reindex

# Options disponibles :
# --chunk-size 300     # Taille des chunks en tokens (~400 caractères)
# --chunk-overlap 50   # Chevauchement entre chunks en tokens
# --force-reindex      # Réinitialiser la base avant d'indexer
# --persist-dir data/chroma_db  # Dossier où stocker la base ChromaDB
```

### 3. Format des documents

Les documents juridiques doivent être placés dans le dossier `data/legal_docs`. Formats supportés :
- PDF (`.pdf`)
- Documents Word (`.docx`)
- Fichiers texte (`.txt`)

Pour une meilleure qualité d'indexation :
- Organisez vos documents en sections claires
- Assurez-vous que les titres de section sont bien formatés
- Incluez des métadonnées (source, auteur, date) dans les noms de fichiers

### 4. Configuration de l'API

Assurez-vous de configurer les variables d'environnement suivantes :
- `MISTRAL_API_KEY`: votre clé API Mistral AI
- `DATABASE_URL`: URL de connexion à la base de données PostgreSQL

### 5. Utilisation du frontend

Les composants frontend inclus dans `frontend-examples/` montrent comment intégrer l'affichage des extraits et sources dans votre interface React.

Pour les intégrer :
1. Copiez les fichiers dans votre projet React
2. Importez et utilisez le composant `ChatResponse` dans votre interface de chat
3. Personnalisez les styles CSS selon l'apparence de votre application

### 6. Maintenir et améliorer la base de connaissances

Pour de meilleurs résultats :
- Réindexez périodiquement vos documents à mesure qu'ils évoluent
- Ajustez la taille des chunks si les réponses sont trop fragmentées
- Surveillez la pertinence des résultats et ajustez les seuils de similarité

### 7. Paramètres de configuration avancés

Pour ajuster les paramètres de l'architecture RAG :

- Dans `chat_service.py`, vous pouvez :
  - Modifier le nombre de documents récupérés (`k=3`)
  - Ajuster le seuil de similarité (`threshold=0.25`)
  - Optimiser le template de prompt
  
- Dans `document_chunker_improved.py`, vous pouvez :
  - Optimiser les séparateurs de texte pour vos documents spécifiques
  - Ajuster les stratégies de pré-traitement du texte

### 8. Logging et monitoring

Le système intègre un logging détaillé pour le débogage et le monitoring :
- Vérifiez les logs pour identifier les problèmes d'indexation
- Surveillez les erreurs lors de la récupération des documents
- Analysez les performances de recherche dans les logs
