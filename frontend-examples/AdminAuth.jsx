import React, { useState } from 'react';
import axios from 'axios';
import './AdminAuth.css';

const AdminAuth = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {      // Appel à l'API d'authentification
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/auth/login`,
        { email, password }
      );

      // Vérifier si l'utilisateur est admin après connexion
      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
          // Récupérer les informations de l'utilisateur
        const userResponse = await axios.get(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/users/me`,
          { headers: { Authorization: `Bearer ${response.data.access_token}` } }
        );

        if (userResponse.data && userResponse.data.is_admin) {
          // L'utilisateur est admin
          localStorage.setItem('isAdmin', 'true');
          onLoginSuccess(userResponse.data);
        } else {
          // L'utilisateur n'est pas admin
          setError("Vous n'avez pas les droits d'administration nécessaires.");
          localStorage.removeItem('token');
        }
      }
    } catch (err) {
      setError('Identifiants incorrects ou erreur de connexion');
      console.error('Erreur de connexion:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-auth-container">
      <div className="admin-auth-card">
        <h2>Administration</h2>
        <p>Connectez-vous pour accéder aux fonctionnalités d'administration</p>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            className="admin-login-button" 
            disabled={isLoading}
          >
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminAuth;
