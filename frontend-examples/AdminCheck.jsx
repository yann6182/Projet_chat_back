import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AdminCheck = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // URL de l'API (à remplacer par votre URL en production)
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  useEffect(() => {
    const checkAdminStatus = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Récupérer le token depuis le localStorage
        const token = localStorage.getItem('token');
          // Appeler l'API pour vérifier si l'utilisateur est admin
        const response = await axios.get(`${apiUrl}/api/auth/check-admin`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          withCredentials: true  // Pour envoyer les cookies
        });
        
        // Vérifier si l'utilisateur est authentifié et admin
        if (response.data && response.data.authenticated) {
          setIsAdmin(response.data.is_admin);
          
          // Si l'utilisateur est admin, stocker cette information
          if (response.data.is_admin) {
            localStorage.setItem('isAdmin', 'true');
          } else {
            localStorage.removeItem('isAdmin');
          }
        } else {
          setIsAdmin(false);
          localStorage.removeItem('isAdmin');
        }
      } catch (err) {
        console.error('Erreur lors de la vérification du statut admin:', err);
        setError('Impossible de vérifier les droits d\'administration');
        setIsAdmin(false);
        localStorage.removeItem('isAdmin');
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAdminStatus();
  }, [apiUrl]);
  
  // Composant de chargement
  if (isLoading) {
    return <div>Vérification des droits d'accès...</div>;
  }
  
  // Composant d'erreur
  if (error) {
    return <div className="error">{error}</div>;
  }
  
  // Affichage basé sur les droits de l'utilisateur
  return (
    <div>
      {isAdmin ? (
        <div className="admin-badge">
          <span>✓ Accès administrateur</span>
          <button onClick={() => window.location.href = '/admin'}>
            Accéder au panneau d'administration
          </button>
        </div>
      ) : (
        <div className="user-badge">
          Vous n'avez pas les droits d'administration
        </div>
      )}
    </div>
  );
};

export default AdminCheck;
