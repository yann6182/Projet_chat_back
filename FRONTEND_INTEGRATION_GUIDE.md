# Guide d'Intégration Frontend pour le Service d'Analyse et de Correction de Documents

Ce guide détaille comment le frontend doit interagir avec l'API backend pour utiliser les fonctionnalités d'analyse et de correction de documents.

## Table des Matières
1.  [Configuration de Base](#configuration-de-base)
2.  [Téléversement de Documents](#1-téléversement-de-documents)
3.  [Analyse de Documents](#2-analyse-de-documents)
4.  [Correction Automatique de Documents](#3-correction-automatique-de-documents)
5.  [Téléchargement de Documents (Originaux ou Corrigés)](#4-téléchargement-de-documents)
6.  [Interrogation de Documents (Optionnel)](#5-interrogation-de-documents)
7.  [Modèles de Données (Schemas Pydantic)](#modèles-de-données)

## Configuration de Base

L'URL de base de l'API est généralement `http://localhost:8000` (ou l'URL de votre déploiement). Tous les points de terminaison décrits ci-dessous sont relatifs à cette URL de base.

## 1. Téléversement de Documents

Pour téléverser un document, le frontend doit envoyer une requête `POST` au point de terminaison `/api/file-analysis/upload`.

-   **Endpoint**: `POST /api/file-analysis/upload`
-   **Type de contenu (Request)**: `multipart/form-data`
-   **Corps de la requête**:
    -   `file`: Le fichier document à téléverser.
-   **Réponse (Success - 200 OK)**: `DocumentUploadResponse`
    ```json
    {
      "document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // UUID unique du document
      "filename": "nom_original_du_fichier.docx"
    }
    ```
-   **Utilisation**:
    1.  L'utilisateur sélectionne un fichier via un champ de type `<input type="file">`.
    2.  Le frontend envoie ce fichier dans un objet `FormData`.
    3.  Conservez le `document_id` retourné, car il sera nécessaire pour les étapes suivantes (analyse, correction).

## 2. Analyse de Documents

Une fois un document téléversé et son `document_id` obtenu, le frontend peut demander son analyse.

-   **Endpoint**: `POST /api/file-analysis/analyze`
-   **Type de contenu (Request)**: `application/json`
-   **Corps de la requête**: `DocumentAnalysisRequest`
    ```json
    {
      "document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
    ```
-   **Réponse (Success - 200 OK)**: `DocumentAnalysisResponse`
    ```json
    {
      "document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "filename": "nom_original_du_fichier.docx",
      "spelling_errors": [
        {
          "word": "eror",
          "position": {"start": 10, "end": 14},
          "suggestions": ["error", "errors"]
        }
      ],
      "grammar_errors": [
        {
          "text": "Il sont",
          "position": {"start": 20, "end": 27},
          "message": "Possible erreur d'accord sujet-verbe.",
          "suggestions": ["Ils sont"]
        }
      ],
      "legal_compliance_issues": [
        {
          "text": "Clause de confidentialité", // Peut être vide si le problème est général
          "position": {"start": 0, "end": 0}, // Peut être {0,0} si non spécifique à un texte
          "issue_type": "Clause manquante",
          "description": "La clause de confidentialité n'a pas été trouvée.",
          "recommendation": "Ajoutez une clause de confidentialité."
        }
      ],
      "overall_compliance_score": 0.85, // Score entre 0.0 et 1.0
      "suggestions": [
        "Corrigez les 1 erreurs d'orthographe identifiées.",
        "Corrigez les 1 erreurs grammaticales identifiées.",
        "Ajoutez une clause de confidentialité.",
        "Mentionnez explicitement 'Junior Entreprise' dans votre document."
      ]
    }
    ```
-   **Utilisation**:
    1.  Envoyez le `document_id` du document à analyser.
    2.  Affichez les résultats à l'utilisateur :
        *   Liste des erreurs d'orthographe avec leurs suggestions.
        *   Liste des erreurs de grammaire avec leurs suggestions.
        *   Liste des problèmes de conformité légale avec descriptions et recommandations.
        *   Le score global de conformité.
        *   Les suggestions générales d'amélioration.

## 3. Correction Automatique de Documents

Après l'analyse, le frontend peut demander une correction automatique du document.

**Note importante**: Le service backend `auto_correct_document` corrige principalement les erreurs d'orthographe et de grammaire. Les problèmes légaux sont signalés avec des recommandations mais ne sont généralement pas auto-corrigés. Si le document original n'est pas un `.txt`, la version corrigée sera sauvegardée en `.txt`.

-   **Endpoint**: `POST /api/file-analysis/correct`
-   **Type de contenu (Request)**: `application/json`
-   **Corps de la requête**: `DocumentCorrectionRequest`
    ```json
    {
      "document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" // ID du document original
    }
    ```
-   **Réponse (Success - 200 OK)**: `DocumentCorrectionResponse` (structure attendue basée sur `document_service.auto_correct_document`)
    ```json
    {
      "original_document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "corrected_document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx_corrected", // ID du document corrigé
      "filename": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx_corrected.txt", // Nom du fichier corrigé, prêt pour le téléchargement
      "corrections_applied": 5, // Nombre de corrections automatiques effectuées
      "corrections_details": [
        "Correction orthographique: 'eror' → 'error'",
        "Correction grammaticale: 'Il sont' → 'Ils sont'"
        // ... autres détails
      ],
      "legal_recommendations": [
        "Clause manquante: La clause de confidentialité n'a pas été trouvée. - Ajoutez une clause de confidentialité."
        // ... autres recommandations légales
      ],
      "status": "corrected"
    }
    ```
-   **Utilisation**:
    1.  Envoyez le `document_id` du document original.
    2.  La réponse contiendra :
        *   `corrected_document_id`: L'identifiant du nouveau document corrigé (différent de l'original).
        *   `filename`: Le nom du fichier corrigé (par exemple, `original_id_corrected.txt`). Utilisez ce nom pour le téléchargement via l'endpoint `/download/{filename}`.
        *   `corrections_details`: Une liste des modifications apportées.
        *   `legal_recommendations`: Rappel des problèmes légaux et recommandations.
    3.  Proposez à l'utilisateur de télécharger le document corrigé.

## 4. Téléchargement de Documents

Ce point de terminaison permet de télécharger soit le document original, soit un document corrigé.

-   **Endpoint**: `GET /api/file-analysis/download/{filename}`
-   **Paramètres de chemin**:
    -   `filename`: Le nom du fichier à télécharger.
        *   Pour un document original : utilisez le `filename` retourné par l'endpoint `/upload`.
        *   Pour un document corrigé : utilisez le `filename` retourné par l'endpoint `/correct`.
-   **Réponse**: Le fichier binaire. Le navigateur devrait initier un téléchargement.
-   **Utilisation**:
    1.  Construisez l'URL complète, par exemple `http://localhost:8000/api/file-analysis/download/xxxxxxxx-xxxx_corrected.txt`.
    2.  Le moyen le plus simple pour le frontend est de créer un lien (`<a>`) avec cet URL et l'attribut `download`, ou de faire `window.location.href = url;`.

## 5. Interrogation de Documents (Optionnel)

Le système permet de poser des questions sur le contenu d'un document téléversé. À chaque requête, une nouvelle conversation est créée automatiquement.

-   **Endpoint**: `POST /api/file-analysis/query`
-   **Type de contenu (Request)**: `application/json`
-   **Corps de la requête**: 
    ```json
    {
      "document_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "query": "Quelles sont les clauses principales de ce contrat ?"
    }
    ```
-   **Réponse (Success - 200 OK)**: `ChatResponse` (défini dans `app.schemas.chat`)
    ```json
    {
      "answer": "Les clauses principales de ce contrat semblent être...",
      "sources": [ // Optionnel, si des sources spécifiques du document sont identifiées
        "source1", "source2", ...
      ],
      "conversation_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // Nouvelle conversation générée automatiquement
      "context": {}, // Informations de contexte additionnelles
      "excerpts": [] // Extraits du document utilisés pour répondre
    }
    ```
-   **Utilisation**:
    1.  Permettez à l'utilisateur de saisir une question concernant un document précédemment téléversé (identifié par son `document_id`).
    2.  Affichez la `response` fournie par l'API.

## Modèles de Données (Schemas Pydantic)

Les structures JSON mentionnées ci-dessus (par exemple, `DocumentAnalysisResponse`, `SpellingError`) sont définies côté backend à l'aide de modèles Pydantic. Le frontend doit s'attendre à recevoir des données conformes à ces structures.

### `DocumentUploadResponse`
```typescript
interface DocumentUploadResponse {
  document_id: string;
  filename: string;
}
```

### `DocumentAnalysisRequest`
```typescript
interface DocumentAnalysisRequest {
  document_id: string;
}
```

### `SpellingError`
```typescript
interface SpellingError {
  word: string;
  position: { start: number; end: number };
  suggestions: string[];
}
```

### `GrammarError`
```typescript
interface GrammarError {
  text: string;
  position: { start: number; end: number };
  message: string;
  suggestions: string[];
}
```

### `LegalComplianceIssue`
```typescript
interface LegalComplianceIssue {
  text: string; // Le segment de texte concerné, peut être vide
  position: { start: number; end: number }; // Position, peut être {0,0} si général
  issue_type: string;
  description: string;
  recommendation: string;
}
```

### `DocumentAnalysisResponse`
```typescript
interface DocumentAnalysisResponse {
  document_id: string;
  filename: string;
  spelling_errors: SpellingError[];
  grammar_errors: GrammarError[];
  legal_compliance_issues: LegalComplianceIssue[];
  overall_compliance_score: number; // 0.0 to 1.0
  suggestions: string[];
}
```

### `DocumentCorrectionRequest`
```typescript
interface DocumentCorrectionRequest {
  document_id: string; // ID du document original
}
```

### `DocumentCorrectionResponse`
```typescript
interface DocumentCorrectionResponse {
  original_document_id: string;
  corrected_document_id: string;
  filename: string; // Nom du fichier corrigé pour téléchargement
  corrections_applied: number;
  corrections_details: string[];
  legal_recommendations: string[];
  status: string; // e.g., "corrected"
}
```

### `ChatResponse` (pour l'interrogation)
```typescript
interface Excerpt {
  content: string;
  source: string;
  page?: number;
}

interface ChatResponse {
  answer: string;
  sources: string[];
  conversation_id: string;
  context?: { [key: string]: string };
  excerpts?: Excerpt[];
  generated_document?: {
    filename: string;
    url: string;
    format: string;
  };
}
```

Ce guide devrait fournir une base solide pour l'intégration frontend. Assurez-vous de gérer correctement les états de chargement, les erreurs réseau et les erreurs API (par exemple, réponses 4xx, 5xx) pour une expérience utilisateur robuste.
