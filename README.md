# Real-Time Collaborative System Design Simulator

> **MVP v1.0** — A web platform for practicing distributed system design interviews collaboratively in real-time.

## Overview

Users design architectures using drag-and-drop components on a WebGL canvas, simulate traffic loads to detect bottlenecks, and collaborate in real-time via CRDT-backed WebSocket sync. Designs are auto-checkpointed every minute and can be replayed.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| State | Zustand |
| Canvas | Three.js (WebGL) |
| Real-Time Sync | Yjs (CRDT) + Redis pub/sub |
| Backend API | FastAPI + Uvicorn |
| Simulation | Python (NumPy) |
| Database | PostgreSQL 16 |
| Cache/Broker | Redis 7 |
| Auth | OAuth 2.0 (Google, GitHub) |
| Deployment | Docker + Railway/Heroku |

## Quick Start (Local Dev)

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- Python 3.11+

### 1. Clone & configure environment
```bash
git clone <repo-url>
cd real-time-system-design-simulator
cp .env.example .env
# Fill in OAuth credentials and secrets in .env
```

### 2. Start all services
```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Simulation Service | http://localhost:8001 |

### 3. Run without Docker (development)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Running Tests

```bash
# Backend unit tests
cd backend && pytest --cov=app tests/

# Frontend unit tests
cd frontend && npm test -- --coverage

# E2E tests (Playwright)
npx playwright test

# Load testing (Locust)
locust -f load_test.py --host=http://localhost:8000
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Settings & env vars
│   │   ├── auth/            # OAuth & JWT sessions
│   │   ├── api/             # REST route handlers
│   │   ├── websocket/       # WS manager & CRDT sync
│   │   └── database/        # Models, schema, session
│   ├── simulation/          # Standalone simulation engine
│   ├── tests/               # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # React UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── store/           # Zustand stores
│   │   ├── types/           # TypeScript type definitions
│   │   ├── utils/           # Helper utilities
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
│
├── docs/                    # PRD, TRD, implementation plan
├── docker-compose.yml
├── .env.example
└── README.md
```

## Architecture

See [docs/TRD.md](docs/TRD.md) for the full technical architecture and [docs/PRD.md](docs/PRD.md) for product requirements.

## Implementation Phases

| Phase | Description | Week |
|-------|-------------|------|
| 1 | Infrastructure & Backend Setup | 1 |
| 2 | Design Management API | 1–2 |
| 3 | Simulation Engine | 2–3 |
| 4 | Real-Time WebSocket & CRDT Sync | 3–4 |
| 5 | Frontend — React Canvas & UI | 3–5 |
| 6 | WebSocket Client & Real-Time Sync | 4–5 |
| 7 | Authentication & User Flow | 5 |
| 8 | Testing & Optimization | 5–6 |
| 9 | Deployment & Documentation | 6 |
