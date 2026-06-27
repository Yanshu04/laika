import React, { useRef, useState } from 'react';

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md'];

export default function UploadZone({ onUpload }) {
  const fileInputRef = useRef(null);
  const [error, setError] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  const validateFiles = (files) => {
    setError('');
    const validFiles = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (!SUPPORTED_EXTENSIONS.includes(ext)) {
        setError(`Unsupported file type: ${ext}. Only PDF, DOCX, TXT, and MD allowed.`);
        return [];
      }
      validFiles.push(file);
    }
    return validFiles;
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const valid = validateFiles(e.target.files);
      if (valid.length > 0) {
        onUpload(valid);
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const valid = validateFiles(e.dataTransfer.files);
      if (valid.length > 0) {
        onUpload(valid);
      }
    }
  };

  return (
    <div 
      className={`upload-zone ${isDragOver ? 'dragover' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input 
        type="file" 
        multiple 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        style={{ display: 'none' }}
        accept=".pdf,.docx,.txt,.md"
      />
      <button 
        type="button" 
        className="upload-btn"
        onClick={() => fileInputRef.current?.click()}
      >
        Upload documents
      </button>
      <p className="upload-tip">Drag & drop files here</p>
      {error && <div className="upload-error">{error}</div>}
    </div>
  );
}
