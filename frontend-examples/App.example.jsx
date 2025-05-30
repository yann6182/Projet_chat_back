import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import AdminPage from './AdminPage';
import AdminCheck from './AdminCheck';
import './AdminCheck.css';
import './App.css';

// Composant de protection des routes administratives
const ProtectedAdminRoute = ({ children }) => {
  const [isAdmin, setIsAdmin] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Vérifier si l'utilisateur est admin
    const checkAdmin = async () => {
      try {
        // Récupérer le token depuis le localStorage
        const token = localStorage.getItem('token');
        
        // Si pas de token, rediriger vers la page de login
        if (!token) {
          setIsAdmin(false);
          setIsLoading(false);
          return;
        }
        
        // Appeler l'API pour vérifier le statut admin
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';        const response = await fetch(`${apiUrl}/api/auth/check-admin`, {
          headers: { 
            Authorization: `Bearer ${token}` 
          },
          credentials: 'include' // Pour envoyer les cookies
        });
        
        const data = await response.json();
        
        // Vérifier le statut admin
        if (data.authenticated && data.is_admin) {
          setIsAdmin(true);
        } else {
          setIsAdmin(false);
        }
      } catch (error) {
        console.error('Erreur lors de la vérification admin:', error);
        setIsAdmin(false);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAdmin();
  }, []);
  
  // Afficher un indicateur de chargement pendant la vérification
  if (isLoading) {
    return <div className="loading">Vérification des droits d'accès...</div>;
  }
  
  // Rediriger vers la page de login si pas admin
  if (!isAdmin) {
    return <Navigate to="/login" replace />;
  }
  
  // Afficher le contenu protégé si admin
  return children;
};

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* Route d'accueil */}
          <Route path="/" element={
            <div className="home-container">
              <h1>Application Juridica</h1>
              <p>Votre assistant juridique intelligent</p>
              <AdminCheck />
            </div>
          } />
          
          {/* Route du chat */}
          <Route path="/chat" element={<div>Interface de chat</div>} />
          
          {/* Route d'administration protégée */}
          <Route path="/admin/*" element={
            <ProtectedAdminRoute>
              <AdminPage />
            </ProtectedAdminRoute>
          } />
          
          {/* Route de login */}
          <Route path="/login" element={<div>Page de connexion</div>} />
          
          {/* Route par défaut (404) */}
          <Route path="*" element={<div>Page non trouvée</div>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
