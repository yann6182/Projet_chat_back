# Guide d'Utilisation de l'Interface de Chat Unifiée

Ce guide explique comment utiliser la nouvelle interface de chat unifiée qui permet de poser des questions en texte libre ou avec un document contextuel directement dans la même conversation.

## Table des matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Fonctionnalités](#fonctionnalités)
4. [API Backend](#api-backend)
5. [Exemple d'utilisation](#exemple-dutilisation)

## Introduction

L'interface de chat unifiée permet aux utilisateurs de :
- Créer de nouvelles conversations avec ou sans document
- Continuer des conversations existantes avec ou sans document additionnel
- Visualiser l'historique des conversations

Cette amélioration permet d'utiliser des documents comme contexte dans n'importe quelle conversation, qu'elle soit nouvelle ou existante.

## Installation

Pour utiliser le composant, importez-le dans votre application :

```jsx
import ChatInterface from './ChatInterface';
import './ChatWithFileUpload.css'; // Styles existants réutilisés
```

## Fonctionnalités

### 1. Conversation avec ou sans document

L'interface unifiée permet de :
- Poser une question simple en texte libre
- Poser une question avec un document joint (PDF, DOCX, TXT)
- Ajouter un document à une conversation existante pour une question spécifique

### 2. Gestion des conversations

- Création de nouvelles conversations
- Liste des conversations existantes
- Sélection et continuation de conversations
- Visualisation de l'historique des messages

## API Backend

L'interface utilise les endpoints suivants :

### Création d'une nouvelle conversation
- Sans fichier : `POST /api/chat/query`
- Avec fichier : `POST /api/chat/query-with-file`

### Continuation d'une conversation existante
- Sans fichier : `POST /api/chat/continue/{conversation_id}`
- Avec fichier : `POST /api/chat/query-with-file` (avec paramètre conversation_id)

### Récupération des conversations et historique
- Liste des conversations : `GET /api/chat/my-conversations`
- Historique d'une conversation : `GET /api/chat/history/{conversation_id}`

## Exemple d'utilisation

Voici un exemple complet d'intégration :

```jsx
import React from 'react';
import ChatInterface from './ChatInterface';

const App = ({ token }) => {
  return (
    <div className="app-container">
      <h1>Assistant Juridique</h1>
      <ChatInterface token={token} />
    </div>
  );
};

export default App;
```

## Personnalisation

Le style de l'interface peut être personnalisé en modifiant le fichier CSS existant `ChatWithFileUpload.css`, qui est utilisé par l'interface unifiée.
