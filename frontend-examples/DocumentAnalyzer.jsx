import React, { useState } from 'react';
import './DocumentAnalyzer.css';

const DocumentAnalyzer = ({ token }) => {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [loading, setLoading] = useState(false);
  const [documentId, setDocumentId] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [correctedDocument, setCorrectedDocument] = useState(null);
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };
  
  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('/api/file-analysis/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setDocumentId(data.document_id);
        setActiveTab('analyze');
      } else {
        alert(`Erreur lors du téléchargement : ${data.detail || 'Erreur inconnue'}`);
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors du téléchargement du document');
    } finally {
      setLoading(false);
    }
  };
  
  const handleAnalyze = async () => {
    if (!documentId) return;
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/file-analysis/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ document_id: documentId }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setAnalysis(data);
      } else {
        alert(`Erreur lors de l'analyse : ${data.detail || 'Erreur inconnue'}`);
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors de l\'analyse du document');
    } finally {
      setLoading(false);
    }
  };
  const handleAskQuestion = async () => {
    if (!documentId || !question.trim()) return;
    
    setLoading(true);
    
    try {
      // Envoyer les données au format JSON pour correspondre au nouveau format de l'endpoint
      const response = await fetch('/api/file-analysis/query', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          document_id: documentId,
          query: question,
          // Pas besoin de conversation_id car le backend en génère un nouveau à chaque fois
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setAnswer(data);
      } else {
        alert(`Erreur lors de la requête : ${data.detail || 'Erreur inconnue'}`);
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors du traitement de votre question');
    } finally {
      setLoading(false);
    }
  };
    const handleCorrectDocument = async () => {
    if (!documentId) return;
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/file-analysis/correct', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ document_id: documentId }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setCorrectedDocument(data);
        alert('Le document a été corrigé avec succès !');
      } else {
        alert(`Erreur lors de la correction : ${data.detail || 'Erreur inconnue'}`);
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors de la correction du document');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="document-analyzer-container">
      <h2>Analyse de Documents Juridiques</h2>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          1. Télécharger
        </button>
        <button 
          className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
          disabled={!documentId}
        >
          2. Analyser
        </button>
        <button 
          className={`tab ${activeTab === 'ask' ? 'active' : ''}`}
          onClick={() => setActiveTab('ask')}
          disabled={!documentId}
        >
          3. Poser une question
        </button>
        <button 
          className={`tab ${activeTab === 'correct' ? 'active' : ''}`}
          onClick={() => setActiveTab('correct')}
          disabled={!documentId || !analysis}
        >
          4. Corriger
        </button>
      </div>
      
      <div className="tab-content">
        {activeTab === 'upload' && (
          <div className="upload-section">
            <p>Sélectionnez un document à analyser (.pdf, .docx, .txt)</p>
            <div className="file-input-container">
              <label className="file-input-label">
                <span>{fileName || 'Choisir un fichier'}</span>
                <input 
                  type="file" 
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.doc,.txt,.pptx,.ppt" 
                />
              </label>
              <button 
                className="upload-button"
                onClick={handleUpload}
                disabled={!file || loading}
              >
                {loading ? 'Téléchargement...' : 'Télécharger'}
              </button>
            </div>
            {documentId && (
              <div className="success-message">
                Document téléchargé avec succès! ID: {documentId}
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'analyze' && (
          <div className="analyze-section">
            <p>Cliquez sur le bouton ci-dessous pour analyser le document téléchargé</p>
            <button 
              className="analyze-button"
              onClick={handleAnalyze}
              disabled={loading}
            >
              {loading ? 'Analyse en cours...' : 'Analyser le document'}
            </button>
            
            {analysis && (
              <div className="analysis-results">
                <h3>Résultats de l'analyse</h3>
                
                <div className="score-section">
                  <div className="compliance-score">
                    <div className="score-label">Score de conformité</div>
                    <div className="score-value">{(analysis.overall_compliance_score * 100).toFixed(0)}%</div>
                  </div>
                </div>
                
                {analysis.spelling_errors.length > 0 && (
                  <div className="error-section">
                    <h4>Erreurs d'orthographe ({analysis.spelling_errors.length})</h4>
                    <ul>
                      {analysis.spelling_errors.map((error, index) => (
                        <li key={`spell-${index}`}>
                          <span className="error-word">{error.word}</span>
                          {error.suggestions.length > 0 && (
                            <span className="suggestions">
                              Suggestions: {error.suggestions.join(', ')}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysis.grammar_errors.length > 0 && (
                  <div className="error-section">
                    <h4>Erreurs grammaticales ({analysis.grammar_errors.length})</h4>
                    <ul>
                      {analysis.grammar_errors.map((error, index) => (
                        <li key={`grammar-${index}`}>
                          <span className="error-text">"{error.text}"</span>
                          <span className="error-message">: {error.message}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysis.legal_compliance_issues.length > 0 && (
                  <div className="error-section">
                    <h4>Problèmes juridiques ({analysis.legal_compliance_issues.length})</h4>
                    <ul>
                      {analysis.legal_compliance_issues.map((issue, index) => (
                        <li key={`legal-${index}`}>
                          <div className="issue-type">{issue.issue_type}</div>
                          <div className="issue-description">{issue.description}</div>
                          <div className="issue-recommendation">
                            Recommandation: {issue.recommendation}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysis.suggestions.length > 0 && (
                  <div className="suggestions-section">
                    <h4>Suggestions d'amélioration</h4>
                    <ul>
                      {analysis.suggestions.map((suggestion, index) => (
                        <li key={`suggestion-${index}`}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'ask' && (
          <div className="ask-section">
            <p>Posez une question sur le contenu du document</p>
            <div className="question-input">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Exemple: Quels sont les problèmes juridiques dans ce document?"
                rows={3}
              />
              <button 
                className="ask-button"
                onClick={handleAskQuestion}
                disabled={!question.trim() || loading}
              >
                {loading ? 'Traitement...' : 'Poser la question'}
              </button>
            </div>
            
            {answer && (
              <div className="answer-section">
                <h3>Réponse</h3>
                <div className="answer-content">
                  {answer.answer}
                </div>
                
                {answer.conversation_id && (
                  <div className="conversation-info">
                    <p>Conversation ID: {answer.conversation_id}</p>
                  </div>
                )}
                
                {answer.sources && answer.sources.length > 0 && (
                  <div className="sources">
                    <h4>Sources</h4>
                    <ul>
                      {answer.sources.map((source, index) => (
                        <li key={`source-${index}`}>{source}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {answer.excerpts && answer.excerpts.length > 0 && (
                  <div className="excerpts">
                    <h4>Extraits pertinents</h4>
                    <ul>
                      {answer.excerpts.map((excerpt, index) => (
                        <li key={`excerpt-${index}`}>
                          <p className="excerpt-content">{excerpt.content}</p>
                          <p className="excerpt-source">Source: {excerpt.source} {excerpt.page ? `(page ${excerpt.page})` : ''}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {answer.generated_document && (
                  <div className="generated-document">
                    <h4>Document généré</h4>
                    <a 
                      href={answer.generated_document.url}
                      className="document-link"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Télécharger {answer.generated_document.format.toUpperCase()} 
                      ({answer.generated_document.filename})
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'correct' && (
          <div className="correct-section">
            <p>Corriger automatiquement les erreurs détectées dans le document</p>
            <button 
              className="correct-button"
              onClick={handleCorrectDocument}
              disabled={loading}
            >
              {loading ? 'Correction en cours...' : 'Corriger le document'}
            </button>
            
            {correctedDocument && (
              <div className="correction-results">
                <h3>Document corrigé</h3>
                <p>
                  {correctedDocument.corrections_applied} corrections ont été appliquées.
                </p>
                <div className="download-section">
                  <a 
                    href={`/api/file-analysis/download/${correctedDocument.filename}`}
                    className="download-link"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Télécharger le document corrigé
                  </a>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentAnalyzer;
