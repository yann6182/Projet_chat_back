# Guide d'Utilisation du Chat avec Upload de Fichier

Ce guide explique comment utiliser le nouveau composant `ChatWithFileUpload` qui permet de poser des questions sur un document téléversé directement dans une conversation.

## Table des matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Utilisation du composant](#utilisation-du-composant)
4. [API Backend](#api-backend)
5. [Exemple complet](#exemple-complet)

## Introduction

Le composant `ChatWithFileUpload` permet aux utilisateurs de:
- Téléverser un fichier (PDF, DOCX, TXT, etc.) et poser des questions sur son contenu
- Continuer une conversation existante
- Visualiser l'historique des conversations

Ce composant s'intègre parfaitement avec le backend existant et utilise une nouvelle API pour combiner le téléversement de fichier et les questions en une seule opération.

## Installation

Pour utiliser le composant, assurez-vous d'avoir importé les fichiers nécessaires:

```jsx
import ChatWithFileUpload from './ChatWithFileUpload';
import './ChatWithFileUpload.css';
```

## Utilisation du composant

Le composant s'utilise de la façon suivante:

```jsx
<ChatWithFileUpload token={userAuthToken} />
```

Où `userAuthToken` est le jeton d'authentification de l'utilisateur.

### Fonctionnalités principales

1. **Création d'une nouvelle conversation avec fichier**
   - Cliquez sur "Nouvelle conversation"
   - Sélectionnez un fichier à téléverser
   - Posez une question sur le contenu du document
   - Le système téléverse le fichier, l'analyse et répond à la question en utilisant le contenu comme contexte

2. **Continuation d'une conversation existante**
   - Sélectionnez une conversation dans la liste
   - Posez une question supplémentaire

3. **Visualisation de l'historique**
   - L'historique des messages est automatiquement chargé lorsque vous sélectionnez une conversation

## API Backend

Le composant utilise l'endpoint suivant:

### `POST /api/chat/query-with-file`

Cet endpoint permet de téléverser un fichier et de poser une question dans une seule opération.

**Paramètres**:
- `file` (form-data): Le fichier à téléverser
- `query` (form-data): La question à poser
- `conversation_id` (form-data, optionnel): L'ID de conversation si on continue une conversation existante

**Réponse**:
```json
{
  "answer": "La réponse à la question...",
  "sources": ["source1", "source2"],
  "conversation_id": "UUID de la conversation",
  "context": {},
  "excerpts": [
    {
      "content": "Extrait de texte pertinent",
      "source": "nom_du_fichier.pdf",
      "page": 1
    }
  ]
}
```

## Exemple complet

Voici un exemple d'intégration complète dans une application:

```jsx
import React, { useState, useEffect } from 'react';
import ChatWithFileUpload from './ChatWithFileUpload';
import './ChatWithFileUpload.css';

function App() {
  const [token, setToken] = useState(null);
  
  useEffect(() => {
    // Récupérer le token depuis le localStorage ou une API d'authentification
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);
  
  if (!token) {
    return <div>Veuillez vous connecter</div>;
  }
  
  return (
    <div className="app-container">
      <h1>Chat avec analyse documentaire</h1>
      <ChatWithFileUpload token={token} />
    </div>
  );
}

export default App;
```

## Personnalisation

Le style du composant peut être personnalisé en modifiant le fichier `ChatWithFileUpload.css`. Le composant utilise une interface responsive qui s'adapte à différentes tailles d'écran.
