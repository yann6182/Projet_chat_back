# Guide d'utilisation : Analyse et correction de documents juridiques

Ce guide explique comment utiliser la nouvelle fonctionnalité d'analyse et de correction de documents juridiques dans l'API Juridica.

## Présentation de la fonctionnalité

Cette fonctionnalité permet aux utilisateurs de :

1. **Télécharger** des documents (PDF, DOCX, TXT)
2. **Analyser** automatiquement les documents pour détecter :
   - Les erreurs d'orthographe
   - Les erreurs grammaticales
   - Les problèmes de conformité juridique
3. **Poser des questions** spécifiques sur le contenu du document
4. **Corriger automatiquement** les erreurs détectées

## Prérequis techniques

### Pour le backend :
- Python 3.10+
- SpaCy avec le modèle français (`fr_core_news_md`)
- PyMuPDF (pour l'extraction de texte PDF)
- docx2txt (pour l'extraction de texte DOCX)

### Dépendances à installer :
```bash
pip install spacy python-docx docx2txt pymupdf
python -m spacy download fr_core_news_md
```

## Guide d'utilisation de l'API

### 1. Télécharger un document

**Endpoint :** `POST /api/file-analysis/upload`

**Headers requis :**
- `Authorization: Bearer <token>`

**Corps de la requête :**
- `file`: Le fichier à télécharger (multipart/form-data)

**Réponse :**
```json
{
  "document_id": "uuid-du-document",
  "filename": "nom-du-fichier.pdf",
  "status": "uploaded"
}
```

### 2. Analyser un document

**Endpoint :** `POST /api/file-analysis/analyze`

**Headers requis :**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Corps de la requête :**
```json
{
  "document_id": "uuid-du-document"
}
```

**Réponse :**
```json
{
  "document_id": "uuid-du-document",
  "filename": "nom-du-fichier.pdf",
  "spelling_errors": [
    {
      "word": "enterprize",
      "position": {"start": 12, "end": 22},
      "suggestions": ["entreprise", "enterprise"]
    }
  ],
  "grammar_errors": [
    {
      "text": "une document",
      "position": {"start": 5, "end": 17},
      "message": "Problème d'accord en genre",
      "suggestions": ["un document"]
    }
  ],
  "legal_compliance_issues": [
    {
      "text": "TVA",
      "position": {"start": 120, "end": 123},
      "issue_type": "Mention légale incomplète",
      "description": "La TVA est mentionnée mais le numéro de TVA n'est pas précisé.",
      "recommendation": "Ajoutez le numéro de TVA intracommunautaire."
    }
  ],
  "overall_compliance_score": 0.85,
  "suggestions": [
    "Corrigez les 2 erreurs d'orthographe identifiées.",
    "Mentionnez explicitement 'Junior Entreprise' dans votre document.",
    "Ajoutez le numéro de TVA intracommunautaire."
  ]
}
```

### 3. Poser une question sur le document

**Endpoint :** `POST /api/file-analysis/query`

**Headers requis :**
- `Authorization: Bearer <token>`

**Corps de la requête :**
- `document_id`: L'identifiant du document (form-data)
- `query`: La question à poser sur le document (form-data)
- `conversation_id`: Optionnel, pour continuer une conversation existante (form-data)

**Réponse :**
```json
{
  "answer": "D'après le document, la Junior-Entreprise doit mentionner son numéro de TVA intracommunautaire lorsqu'elle fait référence à la TVA dans ses communications officielles.",
  "conversation_id": "id-de-la-conversation",
  "sources": ["nom-du-fichier.pdf"],
  "excerpts": [
    {
      "content": "...extrait pertinent du document...",
      "source": "nom-du-fichier.pdf",
      "page": null
    }
  ]
}
```

### 4. Corriger un document

**Endpoint :** `POST /api/file-analysis/correct`

**Headers requis :**
- `Authorization: Bearer <token>`

**Corps de la requête :**
- `document_id`: L'identifiant du document (form-data)

**Réponse :**
```json
{
  "original_document_id": "uuid-du-document-original",
  "corrected_document_id": "uuid-du-document-corrigé",
  "filename": "uuid-du-document-corrigé.pdf",
  "corrections_applied": 5,
  "status": "corrected"
}
```

### 5. Télécharger un document corrigé

**Endpoint :** `GET /api/file-analysis/download/{filename}`

**Headers requis :**
- `Authorization: Bearer <token>`

**Réponse :** Le fichier binaire du document corrigé

## Utilisation avec l'interface utilisateur

L'interface utilisateur `DocumentAnalyzer` permet d'accéder à toutes ces fonctionnalités de manière intuitive et est organisée en 4 onglets :

1. **Télécharger** : Permet de sélectionner et d'envoyer un document
2. **Analyser** : Affiche les résultats de l'analyse du document
3. **Poser une question** : Permet d'interagir avec le contenu du document
4. **Corriger** : Permet de corriger automatiquement les erreurs détectées

Pour intégrer cette interface dans votre application React, utilisez le composant `DocumentAnalyzer` :

```jsx
import React from 'react';
import DocumentAnalyzer from './DocumentAnalyzer';

function MyApp() {
  const userToken = "token-d-authentification";
  
  return (
    <div className="app">
      <h1>Mon Application Juridique</h1>
      <DocumentAnalyzer token={userToken} />
    </div>
  );
}

export default MyApp;
```

## Considérations importantes

- Le système actuel utilise SpaCy pour l'analyse linguistique, qui offre des capacités de base. Pour une détection plus avancée des erreurs, envisagez d'intégrer des services spécialisés.
- Pour les documents volumineux, l'analyse peut prendre du temps. Envisagez d'implémenter un traitement asynchrone avec notifications.
- Les corrections automatiques sont basiques et peuvent ne pas capturer tous les problèmes. Proposez toujours à l'utilisateur de vérifier le document corrigé.
- Les fonctionnalités de conseils juridiques s'appuient sur le modèle RAG existant et sont limitées à la connaissance encodée dans la base vectorielle.

## Améliorations futures possibles

- Intégration avec des correcteurs orthographiques professionnels
- Extraction et validation automatique des informations juridiques clés (ex: numéros SIRET, mentions légales)
- Comparaison côte à côte des documents originaux et corrigés
- Édition collaborative des documents avec suivi des modifications
- Création de modèles de documents juridiques à partir des analyses
