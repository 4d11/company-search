# app/main.py

import csv
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from backend.db import database
from backend.routes import query


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    if not db.query(database.Settings).get("seeded"):
        seed_database(db)

        db.add(database.Settings(setting_name="seeded"))
        db.commit()
        db.close()
    yield
    # Clean up...


app = FastAPI(lifespan=lifespan)


def seed_database(db: Session):
    # Add company_id column if it doesn't exist
    try:
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
        db.commit()
    except Exception as e:
        print(f"Note: Could not add company_id column (may already exist): {e}")
        db.rollback()

    # Clear existing data
    db.execute(text("TRUNCATE TABLE companies CASCADE;"))
    db.commit()

    # Load companies from CSV
    csv_path = Path(__file__).parent / "backend" / "db" / "B2B_SaaS_2021-2022.csv"

    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as file:
            # Skip the first line (title line)
            next(file)
            csv_reader = csv.DictReader(file)

            companies = []
            for row in csv_reader:
                company = database.Company(
                    company_name=row.get('Company Name', ''),
                    company_id=int(row.get('Company ID', 0)) if row.get('Company ID', '').isdigit() else None,
                    city=row.get('City', ''),
                    description=row.get('Description', ''),
                    website_url=row.get('Website URL', ''),
                    website_text=row.get('Website Text', ''),
                )
                companies.append(company)

            db.bulk_save_objects(companies)
            db.commit()
            print(f"Loaded {len(companies)} companies from CSV")
    else:
        print(f"CSV file not found at {csv_path}")


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
