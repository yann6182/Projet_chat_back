# Guide de la fonctionnalité de génération automatique des titres

Cette documentation détaille la nouvelle fonctionnalité de génération automatique des titres et de catégorisation des conversations après le premier échange, similaire à ce que propose ChatGPT.

## Présentation générale

Après l'échange initial entre l'utilisateur et l'assistant (première question et première réponse), le système analyse automatiquement cet échange pour :

1. Générer un titre concis et pertinent pour la conversation
2. Assigner la conversation à une catégorie appropriée parmi les catégories prédéfinies

Ces informations sont ensuite enregistrées dans la base de données et disponibles pour le frontend sans requête supplémentaire.

## Fonctionnement technique

### Détection du premier échange

Dans la méthode `process_query()` du service `ChatService`, après l'enregistrement de la réponse en base de données, le système vérifie s'il s'agit de la première question de la conversation :

```python
# Vérifier si c'est le premier échange (1 question + 1 réponse)
question_count = db.query(Question).filter(
    Question.conversation_id == db_conversation.id
).count()

if question_count == 1:
    logger.info(f"Premier échange détecté pour la conversation {conversation_id}, mise à jour des métadonnées...")
    await self.update_conversation_metadata(conversation_id, db)
```

### Génération du titre et de la catégorie

La méthode `update_conversation_metadata()` :

1. Récupère la première question et la première réponse de la conversation
2. Appelle la méthode `generate_smart_title()` qui utilise le LLM pour analyser les textes
3. Met à jour les champs `title` et `category` de l'objet `Conversation` en base de données

### Appel au modèle LLM

La méthode `generate_smart_title()` construit un prompt spécifique pour le modèle Mistral AI :

```python
prompt = f"""Analyse la question suivante et sa réponse, puis:
1. Génère un titre concis en français (maximum 50 caractères) qui résume bien le sujet
2. Classe cette conversation dans une de ces catégories: {', '.join(categories)}

Descriptions des catégories:
- treasury: {category_descriptions["treasury"]}
- organisational: {category_descriptions["organisational"]}
- legal: {category_descriptions["legal"]}
- general: {category_descriptions["general"]}
- other: {category_descriptions["other"]}

Question: {query}

Réponse: {response}

Réponds exactement au format JSON suivant:
{{
  "title": "Titre concis",
  "category": "catégorie choisie"
}}
"""
```

Le modèle renvoie une réponse au format JSON contenant le titre et la catégorie, qui sont ensuite extraits et validés avant d'être utilisés.

### Mécanisme de fallback

En cas d'erreur lors de l'appel au modèle ou du traitement de la réponse, le système utilise deux méthodes de secours pour garantir un comportement robuste :

1. `_generate_title()` : Génère un titre simple basé sur le début de la question
2. `_determine_category()` : Détermine une catégorie en fonction de mots-clés dans la question

## Catégories disponibles

Les catégories prédéfinies dans le système sont :

| Catégorie | Description |
|-----------|-------------|
| treasury | Finance, comptabilité, budget, TVA, trésorerie |
| organisational | Structure, organisation, management, équipe, gestion |
| legal | Juridique, légal, contrats, règlements |
| general | Questions générales sur l'entreprise |
| other | Autres sujets |

## Intégration avec le frontend

### Récupération des conversations

Le frontend peut continuer à utiliser l'endpoint existant pour récupérer les conversations :

```javascript
// GET /api/chat/conversations
const conversations = await api.getConversations();
```

Chaque objet conversation contient maintenant un titre plus descriptif et une catégorie pertinente :

```javascript
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Obligations légales pour création d'une JE",  // Titre généré
  "category": "legal",  // Catégorie déterminée
  "created_at": "2023-06-01T10:30:00Z",
  "updated_at": "2023-06-01T10:32:15Z"
}
```

### Affichage et filtrage

Le frontend peut utiliser ces informations pour :

1. **Afficher des titres pertinents** dans la liste des conversations
2. **Organiser les conversations** par catégorie
3. **Filtrer les conversations** selon leur catégorie

Exemple de composant React pour le filtrage par catégorie :

```jsx
function ConversationList() {
  const [conversations, setConversations] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  
  useEffect(() => {
    async function fetchData() {
      const data = await api.getConversations();
      setConversations(data);
    }
    fetchData();
  }, []);
  
  const filteredConversations = selectedCategory === 'all' 
    ? conversations 
    : conversations.filter(conv => conv.category === selectedCategory);
    
  const categories = [
    { id: 'all', label: 'Toutes les conversations' },
    { id: 'treasury', label: 'Finance & Trésorerie' },
    { id: 'organisational', label: 'Organisation & Management' },
    { id: 'legal', label: 'Juridique' },
    { id: 'general', label: 'Général' },
    { id: 'other', label: 'Autres' }
  ];
  
  return (
    <div>
      <div className="category-filter">
        {categories.map(cat => (
          <button 
            key={cat.id}
            className={selectedCategory === cat.id ? 'active' : ''}
            onClick={() => setSelectedCategory(cat.id)}
          >
            {cat.label}
          </button>
        ))}
      </div>
      
      <div className="conversation-list">
        {filteredConversations.map(conv => (
          <ConversationItem 
            key={conv.id}
            title={conv.title}
            category={conv.category}
            date={new Date(conv.created_at)}
            onClick={() => selectConversation(conv.id)}
          />
        ))}
      </div>
    </div>
  );
}
```

## Personnalisation

### Modification des catégories

Pour ajouter ou modifier les catégories disponibles, modifiez les variables `categories` et `category_descriptions` dans la méthode `generate_smart_title()` du fichier `chat_service.py` :

```python
# Liste des catégories disponibles
categories = ["treasury", "organisational", "legal", "general", "other", "nouvelle_categorie"]
category_descriptions = {
    "treasury": "Finance, comptabilité, budget, TVA, trésorerie",
    "organisational": "Structure, organisation, management, équipe, gestion",
    "legal": "Juridique, légal, contrats, règlements",
    "general": "Questions générales sur l'entreprise",
    "other": "Autres sujets",
    "nouvelle_categorie": "Description de la nouvelle catégorie"
}
```

### Ajustement du prompt

Vous pouvez également modifier le prompt envoyé au modèle pour affiner la génération des titres et la catégorisation. Le prompt se trouve dans la méthode `generate_smart_title()`.

### Optimisation du seuil de détection du premier échange

Par défaut, la mise à jour des métadonnées est déclenchée lorsque `question_count == 1`. Si vous souhaitez retarder cette mise à jour (par exemple, après plusieurs échanges pour avoir plus de contexte), vous pouvez modifier cette condition dans la méthode `process_query()`.
