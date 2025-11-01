# app/main.py

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from backend.db import database
from backend.routes import query


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    database.Base.metadata.create_all(bind=database.engine)
    yield
    # Clean up...


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api", tags=["query"])

