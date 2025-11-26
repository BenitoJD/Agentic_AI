## Multi-Agent Hackathon Stack

This repo houses a hackathon-ready, multi-agent demo powered by FastAPI + LangGraph in `backend/` and a React + Vite control room in `frontend/`. Skill packs live under `backend/app/skillpacks` and describe the 25 industry workflows outlined in the brief.

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
   Create a `.env` file (based on the keys referenced in `app/config.py`) to set `OPENAI_API_KEY`, or leave it blank to use the deterministic fallback responses.

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Visit `http://localhost:5173` to chat with the orchestrator in a ChatGPT-style interface.

### Production / Docker

To run the full stack in a more production-like way with Docker:

```bash
docker-compose up --build -d
```

This will:

- Build and run the **backend** on `http://localhost:8000`
- Build and run the **frontend** on `http://localhost:5173`
- Persist the vector store under `backend/data/vector-store` so uploaded documents survive restarts

Make sure you have a `backend/.env` file configured as described below before running compose.

### Tests & Lint

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run test`
- Shared linting configs live alongside each project (`ruff` for Python, ESLint for React).

### Adding New Skill Packs

1. Duplicate an entry in `backend/app/skillpacks/data.py`.
2. (Optional) Implement custom tool adapters in `backend/app/services/toolkit.py`.
3. Restart the backend or call `POST /api/chat` to see the new pack in the selector automatically (no additional wiring needed).

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
- If Ollama is running locally the planner/executor use it; otherwise OpenAI or Gemini (when their API keys are provided) are used, and deterministic heuristics kick in when none are available. Uploaded files via `/api/files` are chunked into the persistent Chroma store using the Ollama `embedding-gemma` model (or OpenAI embeddings as fallback) so you can extend the system with retrieval later.

### Repo Layout

- `backend/`: FastAPI app exposing `/api/packs` and `/api/chat` (JSON responses + LangGraph orchestrator).
- `frontend/`: Vite-based ChatGPT-like UI with Tailwind styling and automatic agent attribution.
- `shared/`: TypeScript definitions shared between frontend code and future generated clients/tests.

