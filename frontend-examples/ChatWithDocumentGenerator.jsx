import React, { useState, useEffect } from 'react';
import DocumentGenerator from './DocumentGenerator';
import './ChatWithDocumentGenerator.css';

const ChatWithDocumentGenerator = ({ token }) => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDocGenerator, setShowDocGenerator] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  
  // Simuler les données de conversation et de question pour l'exemple
  const currentConversation = conversationId ? { id: conversationId } : null;
  const currentQuestion = selectedMessage ? { id: selectedMessage.questionId } : null;

  // Fonction pour envoyer un message
  const sendMessage = async () => {
    if (!currentMessage.trim()) return;
    
    // Ajouter le message de l'utilisateur à la liste
    const userMessage = { 
      id: Date.now(),
      role: 'user', 
      content: currentMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      // Construire l'URL en fonction de si une conversation existe déjà
      const url = '/api/chat/query';
      const queryParams = conversationId ? `?conversation_id=${conversationId}` : '';
      
      // Envoyer le message au backend
      const response = await fetch(`${url}${queryParams}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: currentMessage })
      });
      
    
      
      const data = await response.json();
      
      // Mettre à jour l'ID de conversation si c'est une nouvelle conversation
      if (!conversationId) {
        setConversationId(data.conversation_id);
      }
        // Ajouter la réponse du bot à la liste des messages
      const botMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        excerpts: data.excerpts || [],
        timestamp: new Date(),
        questionId: userMessage.id, // ID de la question associée à cette réponse
        generatedDocument: data.generated_document || null // Informations sur le document généré automatiquement
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Erreur:', error);
      // Afficher un message d'erreur
      setMessages(prev => [
        ...prev, 
        { 
          id: Date.now() + 1, 
          role: 'system', 
          content: "Désolé, une erreur s'est produite lors de l'envoi de votre message.",
          timestamp: new Date()
        }
      ]);
    } finally {
      setCurrentMessage('');
      setIsLoading(false);
    }
  };

  // Gérer l'appui sur Entrée pour envoyer un message
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Gérer le clic sur le bouton "Générer un document" pour un message spécifique
  const handleGenerateDocument = (message) => {
    setSelectedMessage(message);
    setShowDocGenerator(true);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Chat Juridique</h2>
        <div className="chat-actions">
          <button 
            className="new-conversation"
            onClick={() => {
              setConversationId(null);
              setMessages([]);
            }}
          >
            Nouvelle conversation
          </button>
        </div>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p>Posez une question juridique pour commencer...</p>
          </div>
        ) : (
          messages.map((msg) => (            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-content">{msg.content}</div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <h4>Sources:</h4>
                  <ul>
                    {msg.sources.map((source, idx) => (
                      <li key={idx}>{source}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Afficher le lien de téléchargement si un document a été généré automatiquement */}
              {msg.role === 'assistant' && msg.generatedDocument && (
                <div className="message-document">
                  <h4>Document généré:</h4>
                  <a 
                    href={msg.generatedDocument.url} 
                    className="document-download-link"
                    target="_blank" 
                    rel="noopener noreferrer"
                  >
                    <span className="document-icon">{msg.generatedDocument.format === 'pdf' ? '📄' : '📝'}</span>
                    Télécharger le document {msg.generatedDocument.format.toUpperCase()}
                  </a>
                </div>
              )}

              {msg.role === 'assistant' && (
                <div className="message-actions">
                  <button 
                    className="generate-doc-btn"
                    onClick={() => handleGenerateDocument(msg)}
                  >
                    {msg.generatedDocument ? 'Générer un autre document' : 'Générer un document'}
                  </button>
                </div>
              )}
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="message assistant loading">
            <div className="loading-indicator">...</div>
          </div>
        )}
      </div>
      
      <div className="input-container">
        <textarea
          value={currentMessage}
          onChange={(e) => setCurrentMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Posez votre question..."
          disabled={isLoading}
        />
        <button 
          className="send-btn"
          onClick={sendMessage}
          disabled={isLoading || !currentMessage.trim()}
        >
          Envoyer
        </button>
      </div>

      {showDocGenerator && (
        <div className="document-generator-overlay">
          <div className="document-generator-modal">
            <button 
              className="close-btn"
              onClick={() => {
                setShowDocGenerator(false);
                setSelectedMessage(null);
              }}
            >
              &times;
            </button>
            <DocumentGenerator
              conversation={currentConversation}
              question={currentQuestion}
              token={token}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWithDocumentGenerator;
