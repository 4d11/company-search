from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from backend.db import database
from backend.logging_config import setup_logging
from backend.routes import admin, query, research
from backend.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    database.Base.metadata.create_all(bind=database.engine)

    # Auto-seed database if enabled and not already seeded
    if settings.auto_seed_database:
        from scripts.seed import seed_database
        seed_database()

    yield
    # Clean up...


setup_logging()
app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(admin.router)
app.include_router(research.router, prefix="/api", tags=["research"])