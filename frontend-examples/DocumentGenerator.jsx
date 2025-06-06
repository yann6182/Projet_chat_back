import React, { useState } from 'react';
import './DocumentGenerator.css';

const DocumentGenerator = ({ conversation, question, token }) => {
  const [generating, setGenerating] = useState(false);
  const [generatedDoc, setGeneratedDoc] = useState(null);
  const [error, setError] = useState(null);
  const [format, setFormat] = useState('pdf');
  const [title, setTitle] = useState('');
  const [includeHistory, setIncludeHistory] = useState(false);
  const [includeSources, setIncludeSources] = useState(true);

  const generateDocument = async () => {
    setGenerating(true);
    setError(null);
    setGeneratedDoc(null);
    
    // Construire la requête
    const requestBody = {
      format: format,
      include_question_history: includeHistory,
      include_sources: includeSources
    };
    
    // Ajouter les champs conditionnels
    if (conversation?.id) {
      requestBody.conversation_id = conversation.id;
    }
    
    if (question?.id) {
      requestBody.question_id = question.id;
    }
    
    if (title.trim()) {
      requestBody.title = title;
    }
    
    try {
      const response = await fetch('/api/document-generator/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la génération du document');
      }
      
      const data = await response.json();
      setGeneratedDoc(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };
  
  const downloadDocument = () => {
    if (!generatedDoc?.url) return;
    
    // Créer un lien temporaire et simuler un clic
    const link = document.createElement('a');
    link.href = generatedDoc.url;
    link.download = generatedDoc.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <div className="document-generator">
      <h3>Générer un document</h3>
      
      <div className="form-group">
        <label htmlFor="format">Format du document:</label>
        <select 
          id="format" 
          value={format} 
          onChange={(e) => setFormat(e.target.value)}
          disabled={generating}
        >
          <option value="pdf">PDF</option>
          <option value="docx">Word (DOCX)</option>
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="title">Titre du document (facultatif):</label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Laisser vide pour utiliser le titre par défaut"
          disabled={generating}
        />
      </div>
      
      <div className="form-group checkbox">
        <input
          id="include-history"
          type="checkbox"
          checked={includeHistory}
          onChange={(e) => setIncludeHistory(e.target.checked)}
          disabled={generating}
        />
        <label htmlFor="include-history">
          Inclure l'historique complet de la conversation
        </label>
      </div>
      
      <div className="form-group checkbox">
        <input
          id="include-sources"
          type="checkbox"
          checked={includeSources}
          onChange={(e) => setIncludeSources(e.target.checked)}
          disabled={generating}
        />
        <label htmlFor="include-sources">
          Inclure les sources des réponses
        </label>
      </div>
      
      <button 
        className="generate-btn" 
        onClick={generateDocument} 
        disabled={generating || (!conversation?.id && !question?.id)}
      >
        {generating ? 'Génération en cours...' : 'Générer le document'}
      </button>
      
      {error && (
        <div className="error-message">
          <p>Erreur: {error}</p>
        </div>
      )}
      
      {generatedDoc && (
        <div className="generated-document">
          <p>Document généré avec succès !</p>
          <button className="download-btn" onClick={downloadDocument}>
            Télécharger {generatedDoc.filename}
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentGenerator;
