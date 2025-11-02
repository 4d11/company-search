from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from backend.db import database
from backend.routes import admin, query
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


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Production (backend serving frontend)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(admin.router)