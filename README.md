# Personal Knowledge Agent

An AI agent for your own documents: upload PDFs/text/markdown into
collections, then ask questions in natural language. Instead of a fixed
retrieve-then-answer pipeline, the agent decides at runtime whether to
search documents, read a whole file, list what's in a collection, look
something up by filename, or recall earlier conversation — chaining tool
calls as needed, with citations back to the source document and page.

## Running with Docker (recommended)

Requires [Docker](https://www.docker.com/) and a running local
[Ollama](https://ollama.com/) instance (Ollama itself runs on your host
machine, not in a container — see below).

```bash
ollama pull nomic-embed-text
ollama pull qwen3:8b

cp .env.example .env   # set POSTGRES_PASSWORD and SECRET_KEY

docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Postgres and ChromaDB data persist in Docker volumes across restarts.

Database migrations run automatically on backend startup.

**Why Ollama isn't containerized:** Docker Desktop on macOS doesn't pass
GPU/Metal acceleration through to containers, so a Dockerized Ollama would
be significantly slower for no benefit. The backend container reaches your
host's Ollama via `host.docker.internal:11434`.

## Running locally (without Docker)

Faster iteration loop for backend development; uses SQLite instead of
Postgres.

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

```bash
cd frontend
npm install
npm run dev
```

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL (SQLite for local dev)
- **AI:** Ollama (`qwen3:8b` for chat, `nomic-embed-text` for embeddings), ChromaDB for vector storage
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Query
