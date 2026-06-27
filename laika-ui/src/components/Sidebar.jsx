import React from 'react';
import DocItem from './DocItem';
import UploadZone from './UploadZone';

export default function Sidebar({ 
  documents, 
  onDeleteDoc, 
  onRetryDoc, 
  onUploadDocs, 
  ollamaStatus 
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1 className="laika-wordmark">LAIKA</h1>
        <p className="sidebar-subtitle">Local AI Knowledge Assistant</p>
      </div>

      <div className="sidebar-content">
        <h2 className="section-title">Knowledge Bases</h2>
        <div className="doc-list-scroll">
          {documents.length === 0 ? (
            <div className="empty-docs-sidebar">
              No documents uploaded yet. Add files to build your local index.
            </div>
          ) : (
            documents.map((doc) => (
              <DocItem 
                key={doc.id} 
                doc={doc} 
                onDelete={onDeleteDoc} 
                onRetry={onRetryDoc}
              />
            ))
          )}
        </div>
      </div>

      <div className="sidebar-bottom">
        <UploadZone onUpload={onUploadDocs} />
        
        <div className="sidebar-footer">
          <div className="ollama-status">
            <span className={`status-dot ${ollamaStatus}`}></span>
            <span className="status-text">
              Ollama: {ollamaStatus === 'connected' ? 'Connected' : ollamaStatus === 'disconnected' ? 'Disconnected' : 'Checking...'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
