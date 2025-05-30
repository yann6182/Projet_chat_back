import React, { useState, useEffect } from 'react';
import ApiService from './api.service';
import './AdminDocumentManager.css';

const AdminDocumentManager = () => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [description, setDescription] = useState('');
  const [isReindexing, setIsReindexing] = useState(false);

  // Fonction pour récupérer la liste des documents
  const fetchDocuments = async () => {
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      const response = await ApiService.listDocuments(token);
      setDocuments(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des documents:', error);
      setUploadError('Impossible de charger les documents sources');
    } finally {
      setIsLoading(false);
    }
  };

  // Charger les documents au chargement du composant
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Gérer l'upload d'un document
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadProgress(0);
    setUploadError('');
    setSuccessMessage('');

    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      await ApiService.uploadDocument(formData, token, (progress) => {
        setUploadProgress(progress);
      });

      setSuccessMessage('Document téléchargé avec succès !');
      setDescription('');
      // Actualiser la liste après un upload réussi
      fetchDocuments();
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      setUploadError(
        error.response?.data?.detail || 
        'Erreur lors du téléchargement du document'
      );
    }
  };

  // Gérer la suppression d'un document
  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(`Voulez-vous vraiment supprimer le document ${filename} ?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      await ApiService.deleteDocument(filename, token);

      setSuccessMessage(`Document ${filename} supprimé avec succès`);
      // Actualiser la liste après suppression
      fetchDocuments();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      setUploadError(
        error.response?.data?.detail || 
        'Erreur lors de la suppression du document'
      );
    }
  };

  // Gérer la réindexation des documents
  const handleReindexDocuments = async () => {
    setIsReindexing(true);
    setUploadError('');
    setSuccessMessage('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      const response = await ApiService.reindexDocuments(token);

      setSuccessMessage('Documents réindexés avec succès !');
      console.log('Résultat de la réindexation:', response.data);
    } catch (error) {
      console.error('Erreur lors de la réindexation:', error);
      setUploadError(
        error.response?.data?.detail || 
        'Erreur lors de la réindexation des documents'
      );
    } finally {
      setIsReindexing(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
    else return (bytes / 1073741824).toFixed(2) + ' GB';
  };

  return (
    <div className="admin-document-manager">
      <h2>Gestion des documents sources</h2>
      
      {/* Section d'upload de document */}
      <div className="upload-section">
        <h3>Ajouter un nouveau document</h3>
        <div className="form-group">
          <label htmlFor="description">Description (optionnel)</label>
          <input 
            type="text" 
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description du document"
          />
        </div>
        <div className="form-group">
          <label htmlFor="file-upload" className="custom-file-upload">
            Sélectionner un fichier
          </label>
          <input 
            id="file-upload" 
            type="file" 
            onChange={handleFileUpload}
            accept=".pdf,.txt,.docx,.doc"
          />
        </div>

        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="progress-container">
            <div 
              className="progress-bar" 
              style={{ width: `${uploadProgress}%` }}
            ></div>
            <span>{uploadProgress}%</span>
          </div>
        )}

        {uploadError && <div className="error-message">{uploadError}</div>}
        {successMessage && <div className="success-message">{successMessage}</div>}
      </div>

      {/* Liste des documents */}
      <div className="documents-list-section">
        <div className="documents-header">
          <h3>Documents disponibles</h3>
          <button 
            className="reindex-button"
            onClick={handleReindexDocuments}
            disabled={isReindexing}
          >
            {isReindexing ? 'Réindexation...' : 'Réindexer les documents'}
          </button>
        </div>
        
        {isLoading ? (
          <div className="loading-message">Chargement des documents...</div>
        ) : documents.length === 0 ? (
          <div className="empty-message">Aucun document disponible</div>
        ) : (
          <ul className="documents-list">
            {documents.map((doc, index) => (
              <li key={index} className="document-item">
                <div className="document-info">
                  <span className="document-name">{doc.filename}</span>
                  <span className="document-size">{formatFileSize(doc.size)}</span>
                  {doc.description && (
                    <span className="document-description">{doc.description}</span>
                  )}
                </div>
                <button 
                  className="delete-button"
                  onClick={() => handleDeleteDocument(doc.filename)}
                >
                  Supprimer
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default AdminDocumentManager;
