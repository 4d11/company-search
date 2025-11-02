# Backend

AI-powered company search backend with semantic vector search and LLM-based query understanding.

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary data store (source of truth)
- **Elasticsearch** - Vector search engine with kNN
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation and settings
- **sentence-transformers** - Generate embeddings for semantic search
- **OpenAI-compatible LLM client** - Query classification, filter extraction, explanations

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/intro.html)
- [Pydantic Documentation](https://docs.pydantic.dev/latest/)

## Setup

### Manual Setup

1. Make sure you are in the backend directory:

   ```bash
   pwd
   # Should show: .../backend
   ```

2. Create environment file:

   ```bash
   cp .env.example .env
   # Edit .env and add your LLM_API_KEY
   ```

3. Ensure you have Python 3.9+ installed (this repo was created with 3.9.16)

4. Install dependencies:

   ```bash
   poetry install
   ```

   ([Install Poetry](https://python-poetry.org/docs/#installation) if you don't have it yet)

5. Start Docker services:

   ```bash
   docker compose up -d
   ```

6. Seed the database:

   ```bash
   poetry run python scripts/seed.py
   ```

7. Start the FastAPI server:

   ```bash
   poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

8. View the API documentation at http://localhost:8000/docs


## Database Seeding

The seeding script (`scripts/seed.py`) loads:
- ~500 companies from `backend/db/B2B_SaaS_2021-2022.csv`
- Reference data from `backend/db/seed_data.json` (industries, locations, target markets)
- Uses LLM to extract attributes (industries, business models, etc.) from company descriptions
- Indexes all data into Elasticsearch for vector search

**First-run detection**: The FastAPI server checks if the database is empty on startup and displays a warning if seeding is needed.

## Reset Docker Container

To completely reset your database and container:

```bash
docker compose down -v
docker volume rm backend_postgres_data
docker compose build --no-cache
docker compose up
```

## Accessing the Database

1. SSH into the postgres container:

   ```bash
   docker ps  # Get the container name
   docker exec -it {container_name} /bin/bash
   ```

2. Open the Postgres interface:

   ```bash
   psql -U postgres harmonicjam
   ```

3. List all tables:

   ```sql
   \dt
   ```

4. Run queries:
   ```sql
   SELECT * FROM companies LIMIT 10;
   ```

## Modifying Tables & Schema

Tables and schemas are dynamically loaded when the FastAPI server starts (see `main.py`).

To modify schemas or add new tables:

1. Edit the models in `backend/db/database.py`
2. Restart the server (or perform a hard reset to re-seed the data)

## API Endpoints

Full API documentation can be found here: http://localhost:8000/docs

## Testing

Run all tests:
```bash
poetry run pytest
```

Run specific test file:
```bash
poetry run pytest tests/routes/test_query.py -v
```

Run with coverage:
```bash
poetry run pytest --cov=backend --cov-report=html
```

Test files are organized by module:
- `tests/routes/` - API endpoint tests
- `tests/logic/` - Business logic tests
- `tests/llm/` - LLM client and extraction tests
- `tests/es/` - Elasticsearch operations tests

## Troubleshooting

### Database seeding fails
```bash
# Reset database completely
./scripts/reset_db.sh
```

### LLM API errors
Check your `.env` file:
- Ensure `LLM_API_KEY` is set correctly
- Ensure `LLM_BASE_URL` is set correctly
