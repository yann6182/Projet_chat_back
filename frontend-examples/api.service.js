import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Options de configuration pour les requêtes
const getAuthHeaders = (token) => ({
  headers: token ? { Authorization: `Bearer ${token}` } : {},
  withCredentials: true // Pour envoyer les cookies
});

export const ApiService = {
  // Authentification
  login: (email, password) => 
    axios.post(`${API_URL}/api/auth/login`, 
      { email, password }
    ),
  
  checkAuth: (token) => 
    axios.get(`${API_URL}/api/auth/check-auth`, 
      getAuthHeaders(token)
    ),
  
  checkAdmin: (token) => 
    axios.get(`${API_URL}/api/auth/check-admin`, 
      getAuthHeaders(token)
    ),
  
  // Profil utilisateur
  getUserProfile: (token) => 
    axios.get(`${API_URL}/api/users/me`, 
      getAuthHeaders(token)
    ),
  
  // Gestion des documents administrateur
  listDocuments: (token) => 
    axios.get(`${API_URL}/api/admin/list-sources`, 
      getAuthHeaders(token)
    ),
  
  uploadDocument: (formData, token, onProgress) => 
    axios.post(`${API_URL}/api/admin/upload-source`, 
      formData, 
      {
        ...getAuthHeaders(token),
        headers: {
          ...getAuthHeaders(token).headers,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: progressEvent => {
          if (onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        }
      }
    ),
  
  deleteDocument: (filename, token) => 
    axios.delete(`${API_URL}/api/admin/delete-source/${filename}`, 
      getAuthHeaders(token)
    ),
  
  reindexDocuments: (token) => 
    axios.post(`${API_URL}/api/admin/reindex-sources`, 
      {}, 
      getAuthHeaders(token)
    ),
  
  // Conversations et chat
  getConversations: (token) => 
    axios.get(`${API_URL}/api/chat/conversations`, 
      getAuthHeaders(token)
    ),
  
  getConversation: (conversationId, token) => 
    axios.get(`${API_URL}/api/chat/conversations/${conversationId}`, 
      getAuthHeaders(token)
    ),
  
  sendMessage: (message, conversationId, token) => 
    axios.post(`${API_URL}/api/chat/conversations/${conversationId || ''}`, 
      { question: message },
      getAuthHeaders(token)
    ),
  
  // Exemple d'utilisation avec des paramètres d'URL
  searchDocuments: (query, token) => 
    axios.get(`${API_URL}/api/documents/search`, {
      ...getAuthHeaders(token),
      params: { query }
    })
};

export default ApiService;
