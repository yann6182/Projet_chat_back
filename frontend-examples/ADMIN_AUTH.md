# Guide d'intégration de l'authentification admin

## Configuration CORS

Pour que le frontend puisse communiquer avec l'API et utiliser correctement les cookies d'authentification, il est important de configurer correctement CORS (Cross-Origin Resource Sharing).

### Configuration côté Backend (FastAPI)

Dans `main.py`, assurez-vous que les options CORS sont correctement configurées :

```python
# Configuration CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # Ajoutez ici l'URL de votre frontend
    "https://votre-domaine-production.com"  # En production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Important pour les cookies d'authentification
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-CSRFToken"],
)
```

### Configuration côté Frontend (React)

Dans vos appels axios ou fetch, n'oubliez pas d'inclure les options pour les cookies et utilisez le préfixe `/api` pour tous les endpoints :

#### Avec Axios :
```javascript
axios.get('http://localhost:8000/api/endpoint', {
  withCredentials: true,  // Important pour envoyer les cookies
  headers: {
    Authorization: `Bearer ${token}`  // Si vous utilisez aussi des tokens
  }
});
```

#### Avec Fetch :
```javascript
fetch('http://localhost:8000/api/endpoint', {
  credentials: 'include',  // Important pour envoyer les cookies
  headers: {
    Authorization: `Bearer ${token}`  // Si vous utilisez aussi des tokens
  }
});
```

## Gestion d'authentification hybride (Cookie + Token)

Le système d'authentification prend en charge une approche hybride :

1. **Token dans l'en-tête Authorization** : Pour les clients comme les applications mobiles ou les SPA
2. **Cookie sécurisé** : Pour une sécurité renforcée contre les attaques XSS et CSRF

L'endpoint `/auth/check-admin` accepte les deux méthodes, ce qui facilite l'intégration dans différents types d'applications frontend.

## Composants React fournis

1. **AdminCheck.jsx** : Composant pour vérifier et afficher le statut admin d'un utilisateur
2. **ProtectedAdminRoute** : Composant HOC pour protéger les routes admin dans React Router

## Résolution des problèmes courants

### 1. Erreur CORS

Si vous rencontrez des erreurs CORS, vérifiez :
- Que l'origine du frontend est bien incluse dans la liste `origins` du backend
- Que `allow_credentials` est défini à `True` côté backend
- Que `withCredentials` (axios) ou `credentials: 'include'` (fetch) est utilisé côté frontend

### 2. Erreur 401 Unauthorized

Si vous recevez des 401 alors que vous pensez être authentifié :
- Vérifiez que le token est valide et pas expiré
- Assurez-vous que le token est correctement envoyé (format `Bearer {token}`)
- Vérifiez que les cookies sont correctement envoyés (secure, samesite, etc.)

### 3. Redirection en boucle

Si vous êtes redirigé en boucle vers la page de login :
- Vérifiez la logique du composant `ProtectedAdminRoute`
- Assurez-vous que l'état `isAdmin` est correctement mis à jour après la vérification
