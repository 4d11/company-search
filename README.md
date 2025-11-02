# Company Search - AI-Powered Investment Research

An intelligent search platform for venture capital professionals to discover companies using natural language queries, structured filters, and portfolio-based recommendations.

To see a detailed reflection of the approach taken, please see - [WRITEUP.md](./WRITEUP.md)

## Overview

This application combines semantic search with LLM-powered query understanding to help investors find relevant companies. It supports three search modes:

- **Basic Search**: Attribute-based filtering (e.g., "fintech startups in NYC with Series A funding")
- **Conceptual Search**: Open-ended queries (e.g., "API-first vertical SaaS for regulated industries")
- **Portfolio Analysis**: Complementary investment recommendations based on existing portfolio

## Architecture

**Backend**: FastAPI with PostgreSQL (source of truth) and Elasticsearch (hybrid vector + term search)
- LLM-based query classification and filter extraction
- Semantic search using sentence transformers (BAAI/bge-m3)
- Batch LLM explanation generation with caching
- User override mechanism for filters

**Frontend**: React + TypeScript with Material-UI
- Natural language query input
- Interactive filter management
- Real-time search results with explanations

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ with Poetry (backend)
- Node.js 18+ with Yarn (frontend)

### Backend Setup
```bash
cd backend
poetry install
docker compose up
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
yarn install
yarn dev
```

Access the application at `http://localhost:5173`

## Testing

Run backend tests:
```bash
cd backend
poetry run pytest
```

Run frontend tests:
```bash
cd frontend
yarn test
```


## Documentation

- [Backend README](./backend/README.md) - API documentation and backend architecture
- [Frontend README](./frontend/README.md) - Frontend setup and component guide

## Tech Stack
**Backend**: FastAPI, PostgreSQL, Elasticsearch, SQLAlchemy, Pydantic, sentence-transformers
**Frontend**: React, TypeScript, Vite, Material-UI, Tailwind CSS
