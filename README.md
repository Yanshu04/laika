# LAIKA: Local AI Knowledge Assistant

LAIKA is a private, offline Q&A tool designed to let you chat with your documents locally. It uses a FastAPI backend, a Streamlit frontend, ChromaDB for semantic search, SQLite for full-text search (FTS), and Ollama for the local LLM.

## Features

- **Document Formats**: Native support for PDF, DOCX, TXT, and MD files.
- **Hybrid Search**: Combines semantic embeddings (ChromaDB) and keyword search (SQLite FTS5) using Reciprocal Rank Fusion (RRF).
- **Multi-turn Chat**: Tracks conversation history and automatically reformulates follow-up queries using the local LLM to preserve context.
- **Detailed Citations**: Interactive UI expanders display the exact referenced text snippets and source details.
- **Customizable**: Tweak search modes, top-k chunks, score threshold, and LLM temperature directly in the UI sidebar.

## Project Structure

```
laika/
├── app/
│   ├── api/             # FastAPI endpoints (docs, chat)
│   ├── services/        # Core logic (parsing, chunking, embedding, LLM)
│   ├── repositories/    # Database layers (SQLite metadata)
│   ├── models/          # Schemas and Pydantic models
│   ├── rag/             # RAG pipeline orchestration
│   └── utils/           # Configuration and logging
├── frontend/            # Streamlit UI app
├── data/                # Local storage (ignored in Git; uploads, ChromaDB, SQLite)
└── tests/               # pytest test suite
```

## Quick Start

### 1. Prerequisites
- Python 3.12 or 3.13
- **Ollama**: Download and install [Ollama](https://ollama.com/). Pull the model you want to use (default is `qwen2.5:3b`):
  ```bash
  ollama pull qwen2.5:3b
  ```
  Ensure Ollama is running in the background.

### 2. Set Up the Environment
Create a virtual environment and install dependencies:
```bash
python -m venv .venv

# Activate venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Backend
Start the FastAPI server on port 8080:
```bash
uvicorn app.main:app --port 8080 --reload
```
You can view the Swagger API docs at `http://localhost:8080/docs`.

### 4. Run the Streamlit UI
In another terminal (with the virtual environment activated), start Streamlit:
```bash
streamlit run frontend/app.py
```
Open `http://localhost:8501` in your browser.

## Running Tests
Run the test suite using pytest:
```bash
python -m pytest
```

## Docker Compose
If you prefer running everything in containers, run:
```bash
docker-compose up --build
```
- **Frontend**: `http://localhost:8501`
- **Backend API**: `http://localhost:8080`
