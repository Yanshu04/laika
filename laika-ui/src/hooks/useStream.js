import { useState, useRef } from 'react';
import { streamQuery } from '../api/client';

export function useStream() {
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [streamSources, setStreamSources] = useState([]);

  // Use refs to avoid stale closures in callbacks
  const textRef = useRef('');
  const sourcesRef = useRef([]);

  const startStream = async (payload, onDoneCallback, onErrorCallback) => {
    setStreaming(true);
    setStreamText('');
    setStreamSources([]);
    textRef.current = '';
    sourcesRef.current = [];

    await streamQuery(
      payload,
      (sources) => {
        sourcesRef.current = sources;
        setStreamSources(sources);
      },
      (token) => {
        textRef.current += token;
        setStreamText(textRef.current);
      },
      () => {
        setStreaming(false);
        if (onDoneCallback) {
          onDoneCallback(textRef.current, sourcesRef.current);
        }
      },
      (error) => {
        setStreaming(false);
        if (onErrorCallback) onErrorCallback(error);
      }
    );
  };

  return {
    streaming,
    streamText,
    streamSources,
    startStream,
  };
}
