# Guide d'utilisation : Génération de documents à partir des réponses

Ce guide explique comment utiliser la nouvelle fonctionnalité permettant de générer des documents PDF ou Word à partir des réponses du chat Juridica.

## Présentation de la fonctionnalité

La fonction de génération de documents permet aux utilisateurs de :
- Créer des rapports PDF ou Word à partir d'une réponse spécifique ou d'une conversation entière
- Inclure ou non les sources utilisées pour générer la réponse
- Personnaliser le titre du document généré
- Télécharger facilement le document généré

Cette fonctionnalité est particulièrement utile pour :
- Exporter des réponses juridiques importantes pour référence future
- Créer des rapports professionnels à partager avec des collègues ou clients
- Archiver des informations importantes sous un format standard

## Prérequis techniques pour le backend

Pour utiliser cette fonctionnalité, les bibliothèques Python suivantes doivent être installées :

```bash
pip install -r requirements-doc-generator.txt
```

Ce fichier contient les dépendances :
- python-docx (pour les documents Word)
- reportlab (pour les documents PDF)

## Architecture de la fonctionnalité

### 1. Service de génération de documents

Le service `DocumentGeneratorService` (dans `app/services/document_generator_service.py`) fournit deux méthodes principales :
- `generate_pdf()` : Génère un document PDF formaté
- `generate_word()` : Génère un document Word (DOCX) formaté

### 2. API Endpoints

Deux endpoints sont disponibles :

#### Générer un document
```
POST /api/document-generator/generate
```

Paramètres du corps de la requête :
```json
{
  "conversation_id": "string",        // ID de la conversation (obligatoire)
  "question_id": "integer",           // ID de la question (facultatif)
  "format": "pdf|docx",               // Format du document (obligatoire)
  "title": "string",                  // Titre personnalisé (facultatif)
  "include_question_history": false,  // Inclure tout l'historique (défaut: false)
  "include_sources": true             // Inclure les sources (défaut: true)
}
```

Réponse :
```json
{
  "filename": "string",  // Nom du fichier généré
  "url": "string"        // URL pour télécharger le document
}
```

#### Télécharger un document généré
```
GET /api/document-generator/download/{filename}
```

Renvoie le fichier du document pour téléchargement.

## Intégration dans le frontend

### Composant DocumentGenerator

Le composant `DocumentGenerator` permet de configurer et de générer un document. Il peut être intégré de différentes manières :

1. **Comme bouton dans une interface de chat** : Permet de générer un document à partir d'une réponse spécifique.
2. **Comme interface indépendante** : Permet de générer un document à partir d'une conversation entière.

### Exemples d'utilisation

#### Bouton "Générer un document" sur chaque réponse

```jsx
<div className="message assistant">
  <div className="message-content">{message.content}</div>
  <div className="message-actions">
    <button 
      className="generate-doc-btn"
      onClick={() => handleGenerateDocument(message)}
    >
      Générer un document
    </button>
  </div>
</div>
```

#### Fenêtre modale pour la configuration du document

```jsx
{showDocGenerator && (
  <div className="document-generator-overlay">
    <div className="document-generator-modal">
      <button className="close-btn" onClick={() => setShowDocGenerator(false)}>
        &times;
      </button>
      <DocumentGenerator
        conversation={currentConversation}
        question={selectedMessage && { id: selectedMessage.questionId }}
        token={authToken}
      />
    </div>
  </div>
)}
```

## Personnalisation des documents générés

Les documents générés incluent :

### Structure du document

- **En-tête** : Titre du document et date de génération
- **Métadonnées** : Informations sur l'utilisateur et le type de document
- **Contenu principal** : Question(s) et réponse(s) formatées
- **Sources** (optionnel) : Liste des sources utilisées pour générer les réponses

### Personnalisation côté backend

Vous pouvez personnaliser davantage les documents générés en modifiant les méthodes `generate_pdf()` et `generate_word()` dans le fichier `document_generator_service.py` :

- Modifier les styles (polices, couleurs, marges, etc.)
- Ajouter un logo ou des en-têtes personnalisés
- Ajouter des sections supplémentaires au document
- Modifier la mise en page

## Considérations importantes

- **Performance** : La génération de documents volumineux peut prendre du temps
- **Stockage** : Les documents générés sont stockés dans le répertoire `data/generated_docs`
- **Sécurité** : Seuls les utilisateurs authentifiés peuvent générer et télécharger des documents
- **Expiration** : Il est recommandé de mettre en place un système de nettoyage périodique des anciens documents

## Améliorations futures possibles

- Ajout d'un logo de l'entreprise dans les documents générés
- Support pour d'autres formats de document (HTML, Markdown)
- Personnalisation des modèles de document via l'interface utilisateur
- Prévisualisation du document avant génération
- Options de partage direct (email, lien de téléchargement temporaire)
