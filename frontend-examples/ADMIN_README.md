# Guide d'intégration du système d'administration pour RAG

Ce dossier contient des composants React pour implémenter un système d'administration permettant de gérer les documents sources du système RAG (Retrieval-Augmented Generation).

## Composants disponibles

1. **AdminAuth.jsx** : Gère l'authentification des administrateurs
2. **AdminDocumentManager.jsx** : Permet de télécharger, lister et supprimer les documents sources
3. **AdminPage.jsx** : Page principale d'administration avec navigation par onglets

## Comment intégrer ces composants dans votre application React

### 1. Installation des dépendances

```bash
npm install axios react-router-dom
```

### 2. Configuration des routes

Dans votre fichier de routage principal (App.jsx ou similaire) :

```jsx
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import AdminPage from './components/AdminPage';

function App() {
  return (
    <Router>
      <Routes>
        {/* Autres routes de votre application */}
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  );
}
```

### 3. Protection des routes administratives

Pour plus de sécurité, vous pouvez implémenter un composant de protection de route :

```jsx
import { Navigate } from 'react-router-dom';

const ProtectedAdminRoute = ({ children }) => {
  const isAuthenticated = localStorage.getItem('token') !== null;
  const isAdmin = localStorage.getItem('isAdmin') === 'true';

  if (!isAuthenticated || !isAdmin) {
    return <Navigate to="/login" />;
  }

  return children;
};

// Utilisation dans les routes
<Route 
  path="/admin" 
  element={
    <ProtectedAdminRoute>
      <AdminPage />
    </ProtectedAdminRoute>
  } 
/>
```

### 4. Configuration de l'URL de l'API

Créez un fichier .env à la racine de votre projet frontend :

```
REACT_APP_API_URL=http://localhost:8000
```

## Fonctionnalités

### Authentification des administrateurs
- Login avec vérification des privilèges administrateur
- Gestion de session par token JWT
- Protection des routes administratives

### Gestion des documents sources
- Téléchargement de documents (PDF, TXT, DOCX)
- Liste des documents disponibles
- Suppression de documents
- Réindexation des documents pour le système RAG

## Notes d'implémentation

1. Tous les appels API incluent le token d'authentification dans les en-têtes
2. Le système vérifie si l'utilisateur connecté a les privilèges administrateur
3. Les erreurs sont gérées et affichées à l'utilisateur de manière claire
4. Le processus de téléchargement affiche une barre de progression

## Extension future

Ce système peut être étendu avec les fonctionnalités suivantes :

1. Visualisation des statistiques d'utilisation du RAG
2. Configuration des paramètres du RAG (seuils, modèles, etc.)
3. Gestion des utilisateurs et de leurs droits d'accès
