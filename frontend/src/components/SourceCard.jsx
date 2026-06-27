import React, { useState } from 'react';

export default function SourceCard({ source, documents = [] }) {
  const [expanded, setExpanded] = useState(false);

  // Look up document ID based on filename
  const matchingDoc = documents.find((d) => d.filename === source.filename);
  const docId = matchingDoc ? matchingDoc.id : 'unknown';
  const shortDocId = docId.length > 8 ? docId.slice(0, 8) : docId;

  const pageInfo = source.page_number && source.page_number !== -1
    ? `(Page ${source.page_number})`
    : '';

  return (
    <div 
      className={`source-card ${expanded ? 'expanded' : ''}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="source-header">
        <span className="source-title">
          📄 {source.filename} {pageInfo}
        </span>
        <span className="source-doc-id">
          ID: {shortDocId}
        </span>
        <span className="source-arrow">
          {expanded ? '▲' : '▼'}
        </span>
      </div>
      {expanded && (
        <div className="source-content" onClick={(e) => e.stopPropagation()}>
          {source.text_snippet}
        </div>
      )}
    </div>
  );
}
