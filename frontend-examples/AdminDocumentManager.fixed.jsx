import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AdminDocumentManager.css';

const AdminDocumentManager = () => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [description, setDescription] = useState('');
  const [isReindexing, setIsReindexing] = useState(false);

  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  const fetchDocuments = async () => {
    setIsLoading(true);
    setUploadError('');
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      console.log('Fetching documents from:', `${apiUrl}/api/admin/list-sources`);
      const response = await axios.get(`${apiUrl}/api/admin/list-sources`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('Documents response:', response.data);
      setDocuments(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des documents:', error);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
      setUploadError('Impossible de charger les documents sources');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadProgress(0);
    setUploadError('');
    setSuccessMessage('');

    // Créer un FormData correctement structuré
    const formData = new FormData();
    formData.append('file', file); // Le nom doit correspondre exactement à ce que le backend attend
    
    if (description) {
      formData.append('description', description);
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      console.log('Uploading file to:', `${apiUrl}/api/admin/upload-source`);
      console.log('File being uploaded:', file.name);
      
      // Log le contenu du FormData pour débogage
      for (let pair of formData.entries()) {
        console.log(pair[0] + ': ' + pair[1]);
      }
      
      const response = await axios.post(`${apiUrl}/api/admin/upload-source`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          // Ne pas définir le Content-Type manuellement, axios le fera correctement
          // pour un FormData avec 'multipart/form-data' et la boundary nécessaire
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        }
      });

      console.log('Upload response:', response.data);
      setSuccessMessage('Document téléchargé avec succès !');
      setDescription('');
      // Actualiser la liste après un upload réussi
      fetchDocuments();
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
      setUploadError(
        error.response?.data?.detail || 
        'Erreur lors du téléchargement du document'
      );
    }
  };

  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(`Voulez-vous vraiment supprimer le document ${filename} ?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      console.log('Deleting document:', filename);
      const response = await axios.delete(`${apiUrl}/api/admin/delete-source/${filename}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('Delete response:', response.data);
      setSuccessMessage(`Document ${filename} supprimé avec succès`);
      // Actualiser la liste après suppression
      fetchDocuments();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
      setUploadError(
        error.response?.data?.detail || 
        'Erreur lors de la suppression du document'
      );
    }
  };

  const handleReindexDocuments = async () => {
    setIsReindexing(true);
    setUploadError('');
    setSuccessMessage('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Non authentifié');
      }

      console.log('Reindexing documents');
      const response = await axios.post(`${apiUrl}/api/admin/reindex-sources`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('Reindex response:', response.data);
      setSuccessMessage('Documents réindexés avec succès !');
    } catch (error) {
      console.error('Erreur lors de la réindexation:', error);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
      setUploadError(
        error.response?.data?.detail || 
        'Erreur lors de la réindexation des documents'
      );
    } finally {
      setIsReindexing(false);
    }
  };

  // Reste du composant inchangé
  
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
  
  // Fonction utilitaire pour formatage de taille
  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
    else return (bytes / 1073741824).toFixed(2) + ' GB';
  }
};

export default AdminDocumentManager;
