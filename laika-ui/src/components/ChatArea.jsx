import React, { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble';

export default function ChatArea({
  messages,
  onSendMessage,
  streaming,
  streamText,
  streamSources,
  searchMode,
  setSearchMode,
  ollamaStatus,
  hasDocuments,
  documents = []
}) {
  const [input, setInput] = useState('');
  const chatBottomRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamText, streaming]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || streaming || ollamaStatus !== 'connected' || !hasDocuments) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isInputDisabled = streaming || ollamaStatus !== 'connected' || !hasDocuments;

  return (
    <div className="chat-area">
      {/* Search Mode Toggle Header */}
      <div className="chat-header">
        <div className="search-mode-toggles">
          <button 
            className={`mode-toggle-btn ${searchMode === 'hybrid' ? 'active' : ''}`}
            onClick={() => setSearchMode('hybrid')}
          >
            Hybrid
          </button>
          <button 
            className={`mode-toggle-btn ${searchMode === 'semantic' ? 'active' : ''}`}
            onClick={() => setSearchMode('semantic')}
          >
            Vector
          </button>
          <button 
            className={`mode-toggle-btn ${searchMode === 'keyword' ? 'active' : ''}`}
            onClick={() => setSearchMode('keyword')}
          >
            Keyword
          </button>
        </div>
      </div>

      {/* Ollama Disconnected Banner */}
      {ollamaStatus === 'disconnected' && (
        <div className="status-banner">
          Ollama not connected — start Ollama to enable chat
        </div>
      )}

      {/* Chat Messages / Main Area */}
      <div className="chat-body">
        {!hasDocuments ? (
          <div className="empty-state-container">
            <div className="empty-state-text">
              Upload a document to start querying
            </div>
          </div>
        ) : messages.length === 0 && !streaming ? (
          <div className="empty-chat-container">
            <div className="empty-chat-title">Ask LAIKA Anything</div>
            <div className="empty-chat-subtitle">Your private knowledge is fully loaded and indexed.</div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg, idx) => (
              <MessageBubble 
                key={idx} 
                message={msg} 
                isStreaming={false} 
                documents={documents}
              />
            ))}
            
            {/* Render active stream message */}
            {streaming && (
              <MessageBubble 
                message={{
                  role: 'assistant',
                  content: streamText,
                  sources: streamSources
                }} 
                isStreaming={true} 
                documents={documents}
              />
            )}
            <div ref={chatBottomRef} />
          </div>
        )}
      </div>

      {/* Chat Input Bar */}
      <div className="chat-footer">
        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              !hasDocuments 
                ? "Upload a document to enable chat..."
                : ollamaStatus !== 'connected'
                ? "Start Ollama to enable chat..."
                : "Ask a question about your documents..."
            }
            disabled={isInputDisabled}
            rows={1}
          />
          <button 
            type="submit" 
            className="send-btn" 
            disabled={isInputDisabled || !input.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
