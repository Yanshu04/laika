import React from 'react';

export default function DocItem({ doc, onDelete, onRetry }) {
  const shortName = doc.filename.length > 25 
    ? doc.filename.slice(0, 22) + '...' 
    : doc.filename;

  const getStatusBadge = () => {
    switch (doc.status) {
      case 'INDEXED':
        return <span className="status-badge status-ready">Ready</span>;
      case 'UPLOADING':
      case 'PROCESSING':
        return <span className="status-badge status-pulsing">Indexing...</span>;
      case 'ERROR':
        return (
          <div className="status-error-container">
            <span className="status-badge status-error">Failed</span>
            <button 
              className="retry-btn" 
              onClick={(e) => {
                e.stopPropagation();
                onRetry(doc.id);
              }}
              title="Retry Indexing"
            >
              🔄
            </button>
          </div>
        );
      default:
        return <span className="status-badge">{doc.status}</span>;
    }
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
      onDelete(doc.id);
    }
  };

  return (
    <div className="doc-item">
      <div className="doc-item-icon">📄</div>
      <div className="doc-item-details">
        <div className="doc-item-name" title={doc.filename}>{shortName}</div>
        <div className="doc-item-meta">
          {getStatusBadge()}
          {doc.page_count && doc.page_count > 0 && (
            <span className="doc-item-pages">• {doc.page_count} pgs</span>
          )}
        </div>
      </div>
      <button className="delete-btn" onClick={handleDelete} title="Delete Document">
        🗑
      </button>
    </div>
  );
}
