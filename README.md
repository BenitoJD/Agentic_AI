## Performance Bottleneck Analyzer

This application helps performance engineers quickly identify application bottlenecks from logs and metrics data. It uses generative AI to analyze log files and metrics, automatically detecting performance issues and providing actionable recommendations.

The stack is powered by FastAPI + LangGraph in `backend/` and a React + Vite interface in `frontend/`.

### Prerequisites

- Python 3.11+
- Node.js 20+

### Quick Start

1. **Backend**
   ```bash
   cd backend
   pip install -e .
   uvicorn app.main:app --reload
   ```
   Create a `.env` file (based on the keys referenced in `app/config.py`) to set your LLM API key (OpenAI, Gemini, or Ollama). See LLM & Embeddings Configuration below.

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Visit `http://localhost:5173` to start analyzing performance bottlenecks. Upload log files (.log, .txt) or metrics files (JSON, CSV) and ask questions about performance issues.

### Production / Docker

To run the full stack in a more production-like way with Docker:

```bash
docker-compose up --build -d
```

This will:

- Build and run the **backend** on `http://localhost:8000`
- Build and run the **frontend** on `http://localhost:5173`
- Persist the vector store under `backend/data/vector-store` so uploaded log/metrics files survive restarts

Make sure you have a `backend/.env` file configured as described below before running compose.

### Tests & Lint

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run test`
- Shared linting configs live alongside each project (`ruff` for Python, ESLint for React).

### Usage

1. **Upload Logs/Metrics**: Use the upload button in the UI to upload log files (.log, .txt) or metrics files (JSON, CSV).
2. **Ask Questions**: Query the system about performance issues, for example:
   - "What bottlenecks do you see in the logs?"
   - "Analyze the performance issues"
   - "What's causing the slow response times?"
   - "Identify memory bottlenecks"
3. **Review Findings**: The AI will identify bottlenecks (CPU, memory, network, database, disk I/O) with severity levels, evidence, and recommendations.

### LLM & Embeddings Configuration

- The backend now supports **Ollama first**, falling back to OpenAI automatically.
- Configure via `.env`:
  ```
  LLM_PREFERENCE=auto        # auto | ollama | openai | gemini
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.1
  OPENAI_API_KEY=sk-...
  OPENAI_MODEL=gpt-4o-mini
  GEMINI_API_KEY=AIza...      # Google Generative AI key
  GEMINI_MODEL=gemini-2.0-flash-lite
  EMBEDDING_PREFERENCE=ollama  # ollama | openai
  OLLAMA_EMBEDDING_MODEL=embedding-gemma:7b
  OPENAI_EMBEDDING_MODEL=text-embedding-3-small
  VECTOR_STORE_PATH=./data/vector-store
  VECTOR_COLLECTION=uploaded_docs
  ```
- If Ollama is running locally the system uses it; otherwise OpenAI or Gemini (when their API keys are provided) are used. Uploaded log/metrics files via `/api/files` are chunked into the persistent Chroma store using embeddings for semantic search during bottleneck analysis.

### Repo Layout

- `backend/`: FastAPI app exposing `/api/chat` and `/api/files` endpoints with LangGraph orchestrator for performance analysis.
- `frontend/`: Vite-based ChatGPT-like UI with Tailwind styling for performance bottleneck analysis.
- `shared/`: TypeScript definitions shared between frontend code and future generated clients/tests.

### Supported File Types

- **Log Files**: `.log`, `.txt` (application logs, error logs, access logs)
- **Metrics Files**: `.json` (Prometheus, custom JSON metrics), `.csv`, `.tsv` (time-series metrics)
- **Other**: `.pdf`, `.docx`, `.xlsx`, `.pptx` (for documentation or reports)

