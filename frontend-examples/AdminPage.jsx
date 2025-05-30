import React, { useState, useEffect } from 'react';
import AdminAuth from './AdminAuth';
import AdminDocumentManager from './AdminDocumentManager';
import './AdminPage.css';

const AdminPage = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentAdmin, setCurrentAdmin] = useState(null);
  const [activeTab, setActiveTab] = useState('documents');

  useEffect(() => {
    // Vérifier si l'utilisateur est déjà authentifié comme admin
    const token = localStorage.getItem('token');
    const isAdmin = localStorage.getItem('isAdmin') === 'true';
    
    if (token && isAdmin) {
      setIsAuthenticated(true);
      // Vous pourriez également charger les informations de l'utilisateur ici
    }
  }, []);

  const handleLoginSuccess = (adminData) => {
    setIsAuthenticated(true);
    setCurrentAdmin(adminData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    setIsAuthenticated(false);
    setCurrentAdmin(null);
  };

  // Rendu conditionnel basé sur l'état d'authentification
  if (!isAuthenticated) {
    return <AdminAuth onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>Panneau d'administration</h1>
        <div className="admin-user-info">
          {currentAdmin && (
            <span>Connecté en tant que {currentAdmin.username}</span>
          )}
          <button onClick={handleLogout} className="logout-button">
            Déconnexion
          </button>
        </div>
      </header>

      <nav className="admin-nav">
        <ul>
          <li 
            className={activeTab === 'documents' ? 'active' : ''}
            onClick={() => setActiveTab('documents')}
          >
            Gestion des documents
          </li>
          <li 
            className={activeTab === 'stats' ? 'active' : ''}
            onClick={() => setActiveTab('stats')}
          >
            Statistiques
          </li>
          <li 
            className={activeTab === 'settings' ? 'active' : ''}
            onClick={() => setActiveTab('settings')}
          >
            Paramètres
          </li>
        </ul>
      </nav>

      <main className="admin-content">
        {activeTab === 'documents' && <AdminDocumentManager />}
        {activeTab === 'stats' && (
          <div className="coming-soon">
            <h2>Statistiques</h2>
            <p>Fonctionnalité à venir prochainement.</p>
          </div>
        )}
        {activeTab === 'settings' && (
          <div className="coming-soon">
            <h2>Paramètres</h2>
            <p>Fonctionnalité à venir prochainement.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminPage;
