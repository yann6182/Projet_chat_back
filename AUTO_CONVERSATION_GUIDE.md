# Guide d'implémentation : Création automatique de conversation

Ce document explique comment utiliser la nouvelle fonctionnalité de création automatique de conversation pour le backend Juridica.

## Fonctionnement

Lorsqu'un utilisateur commence à chatter sans avoir explicitement créé une conversation ou sélectionné une conversation existante, le système crée automatiquement une nouvelle conversation et y associe le message.

Cette modification permet une expérience utilisateur plus fluide, similaire à celle de ChatGPT, où l'utilisateur peut commencer à poser des questions directement sans étapes intermédiaires.

## Modifications effectuées

1. L'endpoint `/api/chat/query` a été modifié pour créer automatiquement une nouvelle conversation si aucun `conversation_id` n'est fourni.
2. Le titre et la catégorie initiaux sont générés automatiquement à partir de la première question.
3. Après le premier échange complet (comme auparavant), le système mettra à jour le titre et la catégorie en utilisant le modèle Mistral LLM pour plus de pertinence.

## Implémentation côté frontend

Voici comment adapter votre frontend pour utiliser cette fonctionnalité :

### 1. Envoi d'une question sans ID de conversation

Pour une nouvelle conversation, envoyez simplement la requête sans inclure de `conversation_id` :

```javascript
// Pour une nouvelle conversation
const response = await fetch('/api/chat/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ query: "Ma question" })
});
```

### 2. Récupération et stockage du nouveau conversation_id

Le backend renverra un `conversation_id` dans la réponse, que vous devez stocker pour les questions suivantes :

```javascript
const data = await response.json();
const conversationId = data.conversation_id;

// Stocker cet ID pour les prochaines interactions
// Par exemple dans le state React ou dans le localStorage
```

### 3. Utilisation du conversation_id pour les messages suivants

Pour continuer la même conversation, utilisez le conversation_id obtenu :

```javascript
// Pour continuer une conversation existante
const response = await fetch(`/api/chat/query?conversation_id=${conversationId}`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ query: "Ma question suivante" })
});
```

### Exemple d'implémentation

Un exemple complet d'implémentation frontend est disponible dans le fichier `frontend-examples/AutomaticConversation.jsx`.

## Points importants à noter

1. **Authentification** : L'utilisateur doit toujours être authentifié pour utiliser cette fonctionnalité.
2. **Gestion des erreurs** : En cas d'erreur lors de la création automatique, la transaction est annulée (rollback).
3. **Titres et catégories** : Le titre initial est basé sur la première question, mais sera amélioré après le premier échange complet.

## Avantages pour l'expérience utilisateur

- Interface plus intuitive, sans friction initiale
- Moins d'étapes pour commencer une conversation
- Comportement similaire aux interfaces de chat modernes (ChatGPT, etc.)
- Conservation de toutes les fonctionnalités existantes (historique, titres intelligents, etc.)
