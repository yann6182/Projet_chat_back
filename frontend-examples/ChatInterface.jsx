import React, { useState, useEffect, useRef } from 'react';
import './ChatWithFileUpload.css'; // On conserve les styles existants

const ChatInterface = ({ token }) => {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null); // Référence pour faire défiler vers le bas

  // Charger les conversations existantes au chargement du composant
  useEffect(() => {
    fetchUserConversations();
  }, []);

  // Charger les messages d'une conversation lorsqu'on sélectionne une conversation
  useEffect(() => {
    if (activeConversationId) {
      fetchConversationHistory(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  // Faire défiler vers le bas lorsque les messages changent
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fonction pour faire défiler vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchUserConversations = async () => {
    try {
      const response = await fetch('/api/chat/my-conversations', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      } else {
        console.error('Erreur lors de la récupération des conversations');
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const fetchConversationHistory = async (conversationId) => {
    try {
      const response = await fetch(`/api/chat/history/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.history) {
          setMessages(data.history);
        }
      } else {
        console.error('Erreur lors de la récupération de l\'historique');
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError("Veuillez entrer une question");
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      let response;
      let data;
      
      // Si un fichier est sélectionné, utiliser l'API query-with-file (pour nouvelle ou existante)
      if (file) {
        // Utiliser l'endpoint query-with-file pour poser une question avec un fichier
        const formData = new FormData();
        formData.append('file', file);
        formData.append('query', query);
        
        // Si on a une conversation active, ajouter son ID
        if (activeConversationId) {
          formData.append('conversation_id', activeConversationId);
        }
        
        response = await fetch('/api/chat/query-with-file', {
          method: 'POST',
          headers:
           {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
      } else if (activeConversationId) {
        // Continuer une conversation existante sans fichier
        response = await fetch(`/api/chat/continue/${activeConversationId}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query
          }),
        });
      } else {
        // Nouvelle conversation sans fichier
        response = await fetch(`/api/chat/query`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query
          }),
        });
      }
      
      data = await response.json();
      
      if (response.ok) {
        // Mettre à jour l'ID de conversation active si c'est une nouvelle conversation
        if (!activeConversationId) {
          setActiveConversationId(data.conversation_id);
          await fetchUserConversations(); // Rafraîchir la liste des conversations
        }
        
        // Ajouter les messages à l'historique
        const newUserMessage = { role: 'user', message: query };
        const newAssistantMessage = { role: 'assistant', message: data.answer };
        setMessages(prevMessages => [...prevMessages, newUserMessage, newAssistantMessage]);
        
        // Réinitialiser les champs
        setQuery('');
        if (file) {
          setFile(null);
          setFileName('');
        }
      } else {
        setError(`Erreur: ${data.detail || 'Une erreur est survenue'}`);
      }
    } catch (error) {
      console.error('Erreur:', error);
      setError('Une erreur est survenue lors de la communication avec le serveur');
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setFile(null);
    setFileName('');
    setQuery('');
  };

  return (
    <div className="chat-with-file-container">
      <div className="sidebar">
        <button className="new-conversation-button" onClick={handleNewConversation}>
          Nouvelle conversation
        </button>
        <div className="conversations-list">
          <h3>Mes conversations</h3>
          {conversations.length === 0 ? (
            <p>Aucune conversation</p>
          ) : (
            <ul>
              {conversations.map((conversation) => (
                <li 
                  key={conversation.uuid}
                  className={activeConversationId === conversation.uuid ? 'active' : ''}
                  onClick={() => setActiveConversationId(conversation.uuid)}
                >
                  {conversation.title}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="chat-area">
        <div className="messages-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="message-role">{msg.role === 'user' ? 'Vous' : 'Assistant'}</div>
              <div className="message-content">{msg.message}</div>
            </div>
          ))}
          <div ref={messagesEndRef} /> {/* Élément invisible pour faire défiler vers le bas */}
        </div>
        
        {/* Formulaire de saisie - assurez-vous qu'il soit toujours visible */}
        <form className="chat-input-area" onSubmit={handleSubmit}>
          <div className="file-upload">
            <label className="file-label">
              {fileName || 'Ajouter un fichier (facultatif)'}
              <input 
                type="file" 
                onChange={handleFileChange}
                accept=".pdf,.docx,.doc,.txt,.pptx,.ppt" 
              />
            </label>
          </div>
          
          <div className="query-input">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Posez votre question..."
              rows={3}
              disabled={loading}
              required
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button 
            type="submit" 
            className="send-button"
            disabled={loading}
          >
            {loading ? 'Traitement en cours...' : 'Envoyer'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
