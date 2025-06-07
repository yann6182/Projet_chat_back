import React, { useState, useEffect } from 'react';
import ChatInterface from './ChatInterface';
import './ChatWithFileUpload.css'; // On réutilise les styles existants

const ChatInterfaceApp = () => {
  const [token, setToken] = useState(null);
  
  useEffect(() => {
    // Récupérer le token depuis le localStorage ou une API d'authentification
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);
  
  if (!token) {
    return <div>Veuillez vous connecter</div>;
  }
  
  return (
    <div className="app-container">
      <h1>Assistant Juridique</h1>
      <p className="app-description">
        Posez vos questions en texte libre ou partagez un document pour obtenir des réponses contextuelles.
      </p>
      <ChatInterface token={token} />
    </div>
  );
};

export default ChatInterfaceApp;
