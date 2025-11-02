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

## Quick Start for Reviewers
### Prerequisites
- Docker & Docker Compose
- Python 3.9+ with Poetry ([install](https://python-poetry.org/docs/#installation))
- Node.js 18+ with Yarn
- OpenAI API key (or compatible)

### 1. Backend Setup (Automated)
1. `cd backend`

2. Update the env vars for the api key in docker-compose.yaml
In my case, I used
```
LLM_API_KEY=???
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```
3. `docker-compose up`
4. Navigate to http://localhost:8000

**IMPORTANT NOTE: It will take up to 5 minutes for the backend to seed 
with all the data so please give it some time! I have cached the extractions 
for the companies so your API_KEY will only be used on the query side**

### 2. Frontend Setup
```bash
cd frontend
yarn install
yarn dev
```

Application: http://localhost:5173

### Example Queries to Try
- **Basic**: "fintech startups in San Francisco"
- **Conceptual**: "API-first vertical SaaS for regulated industries"
- **Portfolio**: "My portfolio has consumer fintech. Suggest complementary B2B investments."

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
