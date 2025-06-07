import React, { useState, useEffect } from 'react';
import DocumentAnalyzer from './DocumentAnalyzer';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  // Vérifier si un token existe déjà dans le localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem('juridica_token');
    if (savedToken) {
      setToken(savedToken);
      setIsLoggedIn(true);
    }
  }, []);
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setToken(data.access_token);
        localStorage.setItem('juridica_token', data.access_token);
        setIsLoggedIn(true);
      } else {
        setError(data.detail || 'Erreur de connexion');
      }
    } catch (error) {
      setError('Erreur de connexion au serveur');
      console.error('Login error:', error);
    }
  };
  
  const handleLogout = () => {
    setIsLoggedIn(false);
    setToken('');
    localStorage.removeItem('juridica_token');
  };
  
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Juridica AI</h1>
        {isLoggedIn && (
          <button className="logout-button" onClick={handleLogout}>
            Déconnexion
          </button>
        )}
      </header>
      
      <main className="app-content">
        {isLoggedIn ? (
          <DocumentAnalyzer token={token} />
        ) : (
          <div className="login-form-container">
            <h2>Connexion</h2>
            {error && <div className="error-message">{error}</div>}
            <form className="login-form" onSubmit={handleLogin}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Mot de passe</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              
              <button type="submit">Se connecter</button>
            </form>
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Juridica AI - Tous droits réservés</p>
      </footer>
    </div>
  );
}

export default App;
