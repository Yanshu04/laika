import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { useStream } from './hooks/useStream';
import { 
  getDocuments, 
  uploadDocuments, 
  deleteDocument, 
  retryDocument, 
  getHealth 
} from './api/client';
import './App.css';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [searchMode, setSearchMode] = useState('hybrid');
  const [ollamaStatus, setOllamaStatus] = useState('checking');
  const [polling, setPolling] = useState(false);

  const {
    streaming,
    streamText,
    streamSources,
    startStream
  } = useStream();

  // Fetch all documents from the backend
  const fetchDocs = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      
      // If any document is in UPLOADING or PROCESSING status, enable polling
      const hasPending = docs.some(
        (doc) => doc.status === 'UPLOADING' || doc.status === 'PROCESSING'
      );
      setPolling(hasPending);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  // Poll for document status updates every 3 seconds while pending
  useEffect(() => {
    fetchDocs();
  }, []);

  useEffect(() => {
    if (!polling) return;

    const interval = setInterval(() => {
      fetchDocs();
    }, 3000);

    return () => clearInterval(interval);
  }, [polling]);

  // Check backend and Ollama status
  const checkHealth = async () => {
    try {
      const health = await getHealth();
      const connected = health.services?.ollama_connected;
      setOllamaStatus(connected ? 'connected' : 'disconnected');
    } catch (err) {
      setOllamaStatus('disconnected');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Handle uploading documents
  const handleUploadDocs = async (files) => {
    try {
      await uploadDocuments(files);
      await fetchDocs();
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  // Handle deleting a document
  const handleDeleteDoc = async (id) => {
    try {
      await deleteDocument(id);
      await fetchDocs();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  // Handle retrying a failed document
  const handleRetryDoc = async (id) => {
    try {
      await retryDocument(id);
      await fetchDocs();
    } catch (err) {
      console.error('Retry failed:', err);
    }
  };

  // Handle sending a user query
  const handleSendMessage = async (text) => {
    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);

    const formattedHistory = messages.map((m) => ({
      role: m.role,
      content: m.content
    }));

    const payload = {
      question: text,
      history: formattedHistory,
      top_k: null,
      score_threshold: null,
      search_mode: searchMode,
      temperature: null
    };

    startStream(
      payload,
      (finalText, finalSources) => {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: finalText, sources: finalSources }
        ]);
      },
      (error) => {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Connection error: ${error.message}`, sources: [] }
        ]);
      }
    );
  };

  return (
    <div className="app-container">
      <Sidebar 
        documents={documents}
        onDeleteDoc={handleDeleteDoc}
        onRetryDoc={handleRetryDoc}
        onUploadDocs={handleUploadDocs}
        ollamaStatus={ollamaStatus}
      />
      <div className="main-content">
        <ChatArea 
          messages={messages}
          onSendMessage={handleSendMessage}
          streaming={streaming}
          streamText={streamText}
          streamSources={streamSources}
          searchMode={searchMode}
          setSearchMode={setSearchMode}
          ollamaStatus={ollamaStatus}
          hasDocuments={documents.length > 0}
          documents={documents}
        />
      </div>
    </div>
  );
}
