# Juridica API - Guide d'installation et d'utilisation

Ce guide détaillé explique comment configurer, installer et lancer le backend de Juridica, une API conçue pour fournir des services de questions-réponses juridiques avec fonctionnalités RAG (Retrieval Augmented Generation).

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration des clés API](#configuration-des-clés-api)
4. [Base de données](#base-de-données)
5. [Lancement du serveur](#lancement-du-serveur)
6. [Fonctionnalités principales](#fonctionnalités-principales)
7. [Génération de titres intelligents](#génération-de-titres-intelligents)
8. [Services RAG](#services-rag)
9. [Dépannage](#dépannage)
10. [API Endpoints](#api-endpoints)

## Prérequis

- Python 3.10+ (3.11 recommandé)
- PostgreSQL 13+
- pip (gestionnaire de paquets Python)
- Git (pour cloner le dépôt)
- Compte Mistral AI pour l'API
- Espace disque pour les bases vectorielles (>1GB recommandé)

## Installation

### 1. Cloner le dépôt

```bash
git clone [URL_DU_REPO]
cd Projet_chat_back
```

### 2. Créer et activer un environnement virtuel

#### Sous Windows
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Sous Linux/MacOS
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
# Pour les fonctionnalités RAG supplémentaires
pip install -r requirements-rag.txt
```

## Configuration des clés API

### 1. Créer un fichier .env dans le dossier app/

Créez un fichier `.env` dans le dossier `app/` avec les informations suivantes:

```env
# Configuration base de données
DATABASE_URL=postgresql://username:password@localhost/juridica_db

# Clé API Mistral (obligatoire pour les fonctionnalités de chat)
MISTRAL_API_KEY=votre_clé_mistral_api

# Configuration JWT pour l'authentification
SECRET_KEY=clé_secrète_pour_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Configuration optionnelle de ChromaDB (pour RAG)
CHROMA_DB_DIR=./data/chroma_db
```

### 2. Obtenir une clé API Mistral

1. Créez un compte sur [https://console.mistral.ai/](https://console.mistral.ai/)
2. Accédez à votre profil et générez une clé API
3. Copiez cette clé API dans votre fichier `.env` (MISTRAL_API_KEY)

## Base de données

### 1. Créer la base de données PostgreSQL

```sql
CREATE DATABASE juridica_db;
CREATE USER juridica_user WITH ENCRYPTED PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE juridica_db TO juridica_user;
```

### 2. Exécuter les migrations Alembic

```bash
alembic upgrade head
```

### 3. Créer un utilisateur administrateur (Optionnel)

```bash
python scripts/create_admin.py --email admin@example.com --password votremotdepasse --username admin
```

## Lancement du serveur

### Démarrage standard

```bash
python run.py
```
ou 
```bash
uvicorn app.main:app --reload --port 10000
```

### Démarrage avec Docker

```bash
docker-compose up -d
```

Le serveur sera accessible à l'adresse http://localhost:10000

## Fonctionnalités principales

### Authentification
L'API utilise JWT (JSON Web Tokens) pour l'authentification. Les tokens expirent après la durée spécifiée dans `.env` (ACCESS_TOKEN_EXPIRE_MINUTES).

### Chat avec RAG
Le système intègre un moteur de recherche vectorielle pour enrichir les réponses du modèle avec des informations juridiques pertinentes.

## Génération de titres intelligents

Après le premier échange dans une conversation, le système génère automatiquement:
- Un titre pertinent basé sur la question et la réponse
- Une catégorie appropriée parmi celles prédéfinies

Ce processus est entièrement automatique et ne nécessite aucune action de l'utilisateur. La catégorisation permet de mieux organiser les conversations dans l'interface utilisateur.

### Catégories disponibles

- `treasury`: Finance, comptabilité, budget, TVA, trésorerie
- `organisational`: Structure, organisation, management, équipe, gestion
- `legal`: Juridique, légal, contrats, règlements
- `general`: Questions générales sur l'entreprise
- `other`: Autres sujets

## Services RAG

Le service RAG (Retrieval Augmented Generation) repose sur deux technologies:
1. **ChromaDB** (principal)
2. **FAISS** (fallback)

### Indexation des documents

Pour indexer de nouveaux documents juridiques dans la base vectorielle:

```bash
# Sur Windows
.\rag_utils.ps1 index

# Sur Linux/MacOS
./rag_utils.sh index
```

Tous les documents présents dans le dossier `data/legal_docs/` seront automatiquement indexés.

### Réindexation

Pour réinitialiser et reconstruire complètement l'index:

```bash
# Sur Windows
.\rag_utils.ps1 reindex

# Sur Linux/MacOS
./rag_utils.sh reindex
```

## Dépannage

### Problèmes de connexion à la base de données

1. Vérifiez que PostgreSQL est en cours d'exécution
2. Assurez-vous que les informations d'identification dans le fichier `.env` sont correctes
3. Vérifiez que l'utilisateur a les droits nécessaires sur la base de données

### Erreurs d'API Mistral

1. Vérifiez que votre clé API est valide et correctement renseignée dans le fichier `.env`
2. Assurez-vous que votre compte Mistral dispose de crédits suffisants
3. Vérifiez les logs pour des erreurs spécifiques

### Problèmes avec les services RAG

1. Assurez-vous que les dépendances RAG sont installées: `pip install -r requirements-rag.txt`
2. Vérifiez que le dossier `data/chroma_db` existe et a les droits d'accès appropriés
3. Réindexez les documents en cas de problème persistant

## API Endpoints

### Authentification
- `POST /api/auth/token` - Obtenir un token d'accès (login)
- `POST /api/auth/register` - Créer un nouveau compte utilisateur

### Utilisateurs
- `GET /api/users/me` - Obtenir les informations de l'utilisateur connecté
- `PUT /api/users/me` - Mettre à jour les informations de l'utilisateur

### Conversations
- `POST /api/chat/query` - Envoyer une question et obtenir une réponse
- `GET /api/chat/conversations` - Liste des conversations de l'utilisateur
- `GET /api/chat/conversation/{conversation_id}` - Historique d'une conversation
- `DELETE /api/chat/conversation/{conversation_id}` - Supprimer une conversation

### Documents
- `POST /api/documents/upload` - Télécharger un document pour le contexte
- `GET /api/documents` - Liste des documents disponibles

### Administration (requiert des droits admin)
- `GET /api/admin/users` - Liste des utilisateurs
- `POST /api/admin/knowledge-base` - Ajouter un document à la base de connaissances
- `GET /api/admin/knowledge-base` - Liste des documents dans la base de connaissances
