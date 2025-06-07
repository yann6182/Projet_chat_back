import React, { useState } from 'react';
import ChatWithFileUpload from './ChatWithFileUpload';
import './ChatWithFileUpload.css';

const ChatWithFileUploadApp = ({ token }) => {
  return (
    <div className="app-container">
      <h1>Chat avec Document Contextuel</h1>
      <p className="app-description">
        Posez des questions en téléversant directement un fichier comme contexte ou continuez une conversation existante.
      </p>
      <ChatWithFileUpload token={token} />
    </div>
  );
};

export default ChatWithFileUploadApp;
