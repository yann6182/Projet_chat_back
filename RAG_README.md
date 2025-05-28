# Chat RAG avec Mistral AI

Ce projet implémente un système RAG (Retrieval-Augmented Generation) basé sur Mistral AI pour un assistant juridique conversationnel.

## ⚠️ Important : Configuration de la clé API Mistral

Pour utiliser le système RAG avec les embeddings Mistral, vous devez obtenir une clé API sur [https://console.mistral.ai/](https://console.mistral.ai/) et la configurer :

1. Copiez le fichier `.env.example` en `.env` à la racine du projet  
2. Ajoutez votre clé API dans le fichier `.env` :
   ```
   MISTRAL_API_KEY=votre_clé_api_ici
   ```
3. Redémarrez l'application

Sans clé API, le système fonctionnera en mode dégradé sans fonctionnalités RAG.

## Architecture

Le système utilise une architecture RAG complète avec deux sources de documents :

1. **Indexation des documents** :
   - Chargement et chunking de documents à partir de différentes sources (.pdf, .txt)
   - Génération d'embeddings avec le modèle Mistral Embed
   - Stockage dans un index vectoriel FAISS pour une recherche efficace

2. **Documents contextuels du front-end** :
   - Possibilité pour le front-end d'envoyer des documents contextuels avec chaque requête
   - Ces documents sont utilisés prioritairement pour enrichir la réponse
   - Utile pour des questions spécifiques sur un document que l'utilisateur est en train de consulter

3. **Recherche sémantique** :
   - Conversion des requêtes utilisateurs en embeddings
   - Recherche par similarité vectorielle des documents pertinents
   - Filtrage et dédoublonnage des résultats

4. **Génération de réponses** :
   - Intégration des documents pertinents (indexés + contextuels) dans le contexte
   - Structuration optimisée du prompt pour LLM
   - Génération de réponses avec le modèle Mistral

## Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet avec :

```
MISTRAL_API_KEY=votre_cle_api_mistral
```

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Indexation des documents

1. Placez vos documents dans le dossier `data/`
2. Exécutez le script d'indexation :

```bash
python scripts/reindex.py --data ./data --force
```

### Documents contextuels fournis par le front-end

L'API prend en charge l'ajout de documents contextuels à chaque requête :

```javascript
// Exemple côté front-end (JavaScript)
const response = await fetch('http://api.example.com/api/chat/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer votre_token_ici'
  },
  body: JSON.stringify({
    query: "Ma question juridique ici",
    context_documents: [
      {
        content: "Article L123-1: Le contenu juridique...",
        source: "Code civil",
        page: 42
      }
    ]
  })
});
```

Ces documents contextuels seront utilisés en priorité pour répondre à la question de l'utilisateur.

### Test du système RAG

Pour tester le système sans démarrer le serveur complet :

```bash
python scripts/test_rag.py --query "Votre question ici" --mode both
```

Options pour `--mode` :
- `search` : teste uniquement la recherche de documents
- `response` : teste la génération de réponse complète
- `both` : teste les deux aspects

### Test avec documents contextuels

Pour tester spécifiquement l'intégration de documents contextuels :

```bash
python scripts/test_context_docs.py --mode direct
```

Options pour `--mode` :
- `direct` : teste directement le service sans passer par l'API (plus rapide pour le développement)
- `api` : teste via l'API REST (nécessite que le serveur soit démarré)

### Lancement de l'API

```bash
python run.py
```

## Structure des fichiers

- `app/services/embedding_service.py` : Service d'embeddings avec Mistral
- `app/services/document_loader.py` : Chargement de documents
- `app/services/document_chunker.py` : Découpage intelligent des documents
- `app/services/chat_service.py` : Service de conversation et génération
- `scripts/reindex.py` : Script d'indexation des documents
- `scripts/test_rag.py` : Script de test du système RAG

## Paramètres ajustables

- **Chunking** : Ajustez la taille des chunks et le chevauchement dans `DocumentChunker`
- **Recherche** : Modifiez le nombre de résultats et le seuil de similarité dans `search()`
- **Génération** : Personnalisez le prompt système dans `_generate_response()`
