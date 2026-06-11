# Local AI Knowledge Assistant (LAIKA)

LAIKA is a fully private, offline, Retrieval-Augmented Generation (RAG) knowledge assistant. It allows you to upload company documents (PDFs and DOCX files), processes and vectorizes them locally, and uses a local Large Language Model (LLM) to answer questions with precise page-level source citations.

---

## Technical Architecture

- **Backend Framework:** FastAPI (Uvicorn server)
- **Vector Database:** ChromaDB (persisted locally in-process)
- **Metadata Database:** SQLite (stores file list, upload timestamps, and parsing status)
- **Embedding Model:** BAAI/bge-small-en-v1.5 (runs locally on CPU via `sentence-transformers`)
- **LLM Runtime:** Ollama running `qwen2.5:7b` (runs locally or in container network)
- **Frontend UI:** Streamlit (dark-themed glassmorphism interface)

---

## Local Development Setup

### Prerequisites

1. **Python 3.12 or 3.13** installed on your system.
2. **Ollama** installed on your host machine.
   - [Download Ollama](https://ollama.com/)
   - Pull the default model:
     ```bash
     ollama pull qwen2.5:7b
     ```
   - Keep Ollama running in the background.

### Step 1: Install Dependencies
Create a virtual environment and install the required libraries:
```bash
# In the laika/ directory
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
```

### Step 2: Run the Backend API
Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
The backend API documentation will be available at `http://localhost:8000/docs`.

### Step 3: Run the Frontend UI
In a separate terminal, start the Streamlit web application:
```bash
streamlit run frontend/app.py
```
Open your browser to `http://localhost:8501`.

---

## Docker Quickstart

To run the entire system inside Docker containers:

```bash
docker-compose up --build
```

- **Frontend Web UI:** `http://localhost:8501`
- **FastAPI backend API:** `http://localhost:8000`
- **ChromaDB & SQLite persistence:** Managed inside Docker volumes.

> [!NOTE]
> The Docker container connects to your host machine's Ollama service using `host.docker.internal` port `11434`. Ensure Ollama is running on your host machine and is accessible (e.g. by setting `OLLAMA_HOST=0.0.0.0` or allowing CORS on your host service if required, though the compose maps default configurations automatically).

---

## Running Automated Tests

To execute the unit and integration tests:

```bash
# In the virtual environment
pytest
```
This runs the tests covering repositories, parsed text outputs, chunking offsets, vector indexing structures, and API endpoints.

---

## Project Structure

```
laika/
├── app/
│   ├── api/             # FastAPI routers
│   ├── services/        # Logic services (Parsing, Chunking, Embeddings, Search, LLM)
│   ├── repositories/    # Database operations (SQLite Metadata Repo)
│   ├── models/          # Schemas (Pydantic models)
│   ├── rag/             # Orchestrates the RAG flow
│   └── utils/           # Configuration and logging helpers
│
├── frontend/            # Streamlit frontend files
│
├── data/                # Data storage directories (Git ignored)
│   ├── uploads/         # Raw uploaded documents
│   ├── processed/       # Cached extracted text blocks
│   └── chroma/          # ChromaDB persistent indexes
│
├── tests/               # Pytest testing files
│
├── requirements.txt     # Dependency list
├── Dockerfile.backend   # FastAPI backend Docker image
├── Dockerfile.frontend  # Streamlit frontend Docker image
└── docker-compose.yml   # Docker Compose orchestration configurations
```
