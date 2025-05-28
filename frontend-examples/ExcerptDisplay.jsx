// ExcerptDisplay.jsx - Composant React pour afficher les extraits de documents

import React, { useState } from 'react';
import './ExcerptDisplay.css'; // Assurez-vous de créer un fichier CSS correspondant

/**
 * Composant pour afficher les extraits de documents utilisés dans la réponse RAG
 * 
 * @param {Object} props
 * @param {Array} props.excerpts - Liste des extraits avec leur contenu et source
 * @param {Array} props.sources - Liste des sources utilisées
 */
const ExcerptDisplay = ({ excerpts, sources }) => {
  const [activeTab, setActiveTab] = useState('excerpts');
  const [expandedExcerpt, setExpandedExcerpt] = useState(null);

  // Si pas d'extraits ou de sources, ne rien afficher
  if (!excerpts?.length && !sources?.length) {
    return null;
  }

  const toggleExpand = (index) => {
    if (expandedExcerpt === index) {
      setExpandedExcerpt(null);
    } else {
      setExpandedExcerpt(index);
    }
  };

  return (
    <div className="excerpt-display">
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'excerpts' ? 'active' : ''}`}
          onClick={() => setActiveTab('excerpts')}
        >
          Extraits ({excerpts?.length || 0})
        </button>
        <button 
          className={`tab ${activeTab === 'sources' ? 'active' : ''}`}
          onClick={() => setActiveTab('sources')}
        >
          Sources ({sources?.length || 0})
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'excerpts' && (
          <div className="excerpts-list">
            {excerpts?.length ? (
              excerpts.map((excerpt, index) => (
                <div 
                  key={index} 
                  className={`excerpt-item ${expandedExcerpt === index ? 'expanded' : ''}`}
                >
                  <div className="excerpt-header" onClick={() => toggleExpand(index)}>
                    <span className="excerpt-source">{excerpt.source}</span>
                    {excerpt.page && (
                      <span className="excerpt-page">Page {excerpt.page}</span>
                    )}
                    <span className="expand-icon">
                      {expandedExcerpt === index ? '▼' : '►'}
                    </span>
                  </div>
                  
                  {(expandedExcerpt === index || !expandedExcerpt) && (
                    <div className="excerpt-content">
                      <p>{excerpt.content}</p>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="no-data">Aucun extrait disponible pour cette réponse.</p>
            )}
          </div>
        )}

        {activeTab === 'sources' && (
          <div className="sources-list">
            {sources?.length ? (
              <ul>
                {sources.map((source, index) => (
                  <li key={index} className="source-item">{source}</li>
                ))}
              </ul>
            ) : (
              <p className="no-data">Aucune source disponible pour cette réponse.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExcerptDisplay;
