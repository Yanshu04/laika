const BASE_URL = 'http://localhost:8000';

export async function getDocuments() {
  const res = await fetch(`${BASE_URL}/api/documents`);
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
}

export async function uploadDocuments(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  const res = await fetch(`${BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status: ${res.status}`);
  }
  return res.json();
}

export async function deleteDocument(id) {
  const res = await fetch(`${BASE_URL}/api/documents/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
  return res.json();
}

export async function retryDocument(id) {
  const res = await fetch(`${BASE_URL}/api/documents/${id}/retry`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Retry failed: ${res.status}`);
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${BASE_URL}/`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function streamQuery(payload, onSources, onToken, onDone, onError) {
  try {
    const response = await fetch(`${BASE_URL}/api/chat/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = '';
    let parsedSources = false;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      accumulated += chunk;

      if (!parsedSources) {
        const newlineIdx = accumulated.indexOf('\n');
        if (newlineIdx !== -1) {
          const firstLine = accumulated.substring(0, newlineIdx);
          if (firstLine.startsWith('__SOURCES__:')) {
            const jsonStr = firstLine.substring('__SOURCES__:'.length);
            try {
              const sources = JSON.parse(jsonStr);
              onSources(sources);
            } catch (err) {
              console.error('Failed to parse sources JSON:', err);
              onSources([]);
            }
          }
          accumulated = accumulated.substring(newlineIdx + 1);
          parsedSources = true;
        }
      }

      // If we already parsed the sources line, stream the remaining buffer and chunks
      if (parsedSources && accumulated.length > 0) {
        onToken(accumulated);
        accumulated = '';
      }
    }

    // Call onToken on any trailing buffer if we hadn't processed it
    if (accumulated.length > 0) {
      onToken(accumulated);
    }
    onDone();
  } catch (error) {
    if (onError) onError(error);
  }
}
