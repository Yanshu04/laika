import React from 'react';
import SourceCard from './SourceCard';

export default function MessageBubble({ message, isStreaming, documents = [] }) {
  const isUser = message.role === 'user';

  const renderContent = () => {
    if (isUser) {
      return <div className="message-text">{message.content}</div>;
    }

    // Assistant message styling
    const lines = message.content.split('\n');
    const firstLine = lines[0] || '';
    const restText = lines.slice(1).join('\n');

    return (
      <div className="message-text assistant-text">
        {firstLine && (
          <div className="assistant-heading">
            {firstLine}
            {isStreaming && lines.length === 1 && <span className="cursor">█</span>}
          </div>
        )}
        {restText && (
          <div className="assistant-body">
            {restText}
            {isStreaming && <span className="cursor">█</span>}
          </div>
        )}
        {isStreaming && !firstLine && !restText && (
          <span className="cursor">█</span>
        )}
      </div>
    );
  };

  return (
    <div className={`message-bubble-container ${isUser ? 'user-container' : 'assistant-container'}`}>
      <div className={`message-bubble ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
        {renderContent()}
      </div>
      
      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="sources-container">
          <div className="sources-title">Cited Sources:</div>
          <div className="sources-list">
            {message.sources.map((src, idx) => (
              <SourceCard key={idx} source={src} documents={documents} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
