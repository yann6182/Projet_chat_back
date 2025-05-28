// ChatResponse.jsx - Exemple d'implémentation React de la réponse du chatbot avec excerpts

import React, { useState } from 'react';
import ExcerptDisplay from './ExcerptDisplay';
import './ChatResponse.css';

/**
 * Composant pour afficher une réponse du chatbot, avec la réponse et les sources
 * 
 * @param {Object} props
 * @param {Object} props.response - La réponse complète du chatbot
 */
const ChatResponse = ({ response }) => {
  const [showSources, setShowSources] = useState(false);

  if (!response) {
    return null;
  }

  const { answer, sources, excerpts } = response;

  return (
    <div className="chat-response">
      <div className="response-content">
        {/* Affichage de la réponse principale */}
        <div className="response-text">
          {answer.split('\n').map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>
        
        {/* Affichage des extraits et sources */}
        {(sources?.length > 0 || excerpts?.length > 0) && (
          <>
            <div className="sources-toggle">
              <button onClick={() => setShowSources(!showSources)}>
                {showSources ? 'Masquer les sources' : 'Afficher les sources et extraits'}
              </button>
            </div>
            
            {showSources && (
              <ExcerptDisplay 
                excerpts={excerpts} 
                sources={sources} 
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatResponse;
