# Backend Setup

This backend uses:

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/intro.html)
- [Pydantic Documentation](https://docs.pydantic.dev/latest/)

## Setup

1. Make sure you are in the backend directory:

   ```bash
   pwd
   # Should show: .../backend
   ```

2. Ensure you have Python 3.9+ installed (this repo was created with 3.9.16)

3. Install dependencies:

   ```bash
   poetry install
   ```

   ([Install Poetry](https://python-poetry.org/docs/#installation) if you don't have it yet)

4. Start the backend and database:

   ```bash
   docker compose up
   ```

5. View the API documentation at http://localhost:8000/docs

6. (Optional for VS Code users) Select your Python Interpreter (CMD+P) to use the Poetry-created environment:
   - Find environments: `poetry env list`
   - Get active environment: `poetry env info`

## Database Seeding

The database will automatically be seeded on first startup (see `main.py`) with data from `backend/db/B2B_SaaS_2021-2022.csv`.

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
