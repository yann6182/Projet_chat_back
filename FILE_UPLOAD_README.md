# Documentation pour l'upload de fichiers avec des questions

La fonctionnalité d'upload de fichiers permet aux utilisateurs de poser des questions sur des documents spécifiques sans avoir à les indexer préalablement dans la base de connaissances. Cette approche est utile pour les cas d'utilisation où l'utilisateur a besoin d'une réponse immédiate sur un document qu'il consulte actuellement.

## Endpoints disponibles

### 1. Poser une question avec des fichiers

```
POST /api/file-chat/query
```

**Paramètres du formulaire:**
- `query` (obligatoire): La question de l'utilisateur
- `conversation_id` (optionnel): ID d'une conversation existante
- `files` (optionnel): Liste des fichiers à analyser (PDF, DOCX, TXT, etc.)

**Headers requis:**
- `Authorization: Bearer {token}` - Token JWT pour authentifier l'utilisateur

**Example de requête avec cURL:**

```bash
curl -X POST "http://localhost:8000/api/file-chat/query" \
     -H "Authorization: Bearer {token}" \
     -F "query=Résumez ce document juridique" \
     -F "files=@/chemin/vers/document.pdf"
```

**Exemple de réponse:**

```json
{
  "answer": "Ce document juridique traite de la réglementation concernant...",
  "sources": ["document.pdf"],
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 2. Continuer une conversation avec des fichiers

```
POST /api/file-chat/continue/{conversation_id}
```

**Paramètres:**
- `conversation_id` (dans l'URL): ID de la conversation existante

**Paramètres du formulaire:**
- `query` (obligatoire): La question de l'utilisateur
- `files` (optionnel): Liste des fichiers à analyser (PDF, DOCX, TXT, etc.)

**Headers requis:**
- `Authorization: Bearer {token}` - Token JWT pour authentifier l'utilisateur

## Formats de fichiers supportés

Le service supporte actuellement les formats de fichiers suivants:

1. **Documents texte**
   - PDF (.pdf)
   - Word (.docx)
   - Texte brut (.txt)
   - Markdown (.md)

2. **Documents code**
   - Python (.py)
   - JavaScript (.js)
   - HTML (.html)
   - CSS (.css)

## Fonctionnement interne

Lorsqu'un utilisateur soumet une question avec des fichiers, le processus suivant se déroule:

1. Les fichiers sont téléchargés et temporairement stockés sur le serveur
2. Le texte est extrait de chaque fichier selon son format
3. Le texte extrait est transformé en documents contextuels
4. Ces documents sont combinés avec les résultats de la recherche vectorielle (si disponible)
5. Le modèle de langage génère une réponse basée sur tous les documents pertinents

## Limites actuelles

- La taille maximale de fichier est limitée à 50Mo par défaut
- Le service ne traite pas actuellement les images contenues dans les documents
- Le support pour extraire des tableaux des PDF/DOCX est limité

## Exemple d'utilisation avec le script de test

Pour tester la fonctionnalité, vous pouvez utiliser le script `test_file_upload.py` fourni:

```bash
python scripts/test_file_upload.py --file chemin/vers/document.pdf --query "Analyse ce document juridique"
```

Pour utiliser un token d'authentification:

```bash
python scripts/test_file_upload.py --file chemin/vers/document.pdf --query "Analyse ce document juridique" --token "votre-token-jwt"
```
