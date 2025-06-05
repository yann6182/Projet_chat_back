// Exemple d'implémentation côté frontend pour la création automatique de conversation

// Service d'API pour interagir avec le backend
const chatService = {
  // Fonction pour envoyer une question et obtenir une réponse
  async sendMessage(message, conversationId = null, contextDocuments = []) {
    const url = '/api/chat/query';
    
    const requestBody = {
      query: message,
      context_documents: contextDocuments
    };
    
    // Ajouter l'ID de conversation uniquement s'il est défini
    const queryParams = conversationId ? `?conversation_id=${conversationId}` : '';
    
    
  }
  
  // Autres méthodes pour gérer les conversations...
};

// Exemple de composant React pour le chat
function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Fonction pour envoyer un message
  const sendMessage = async () => {
    if (!currentMessage.trim()) return;
    
    // Ajouter le message de l'utilisateur à la liste
    const userMessage = { 
      role: 'user', 
      content: currentMessage 
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      // Envoyer le message au backend
      // Si conversationId est null, une nouvelle conversation sera créée automatiquement
      const response = await chatService.sendMessage(currentMessage, conversationId);
      
      // Mettre à jour l'ID de conversation si c'est une nouvelle conversation
      if (!conversationId) {
        setConversationId(response.conversationId);
      }
      
      // Ajouter la réponse du bot à la liste des messages
      const botMessage = {
        role: 'assistant',
        content: response.message,
        sources: response.sources,
        excerpts: response.excerpts
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      // Gérer l'erreur
      const errorMessage = {
        role: 'system',
        content: "Désolé, une erreur s'est produite lors de l'envoi de votre message."
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setCurrentMessage('');
      setIsLoading(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
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
          </div>
        ))}
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
          onClick={sendMessage}
          disabled={isLoading || !currentMessage.trim()}
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}
