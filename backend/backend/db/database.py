# app/database.py
import os
from datetime import datetime
from typing import Union

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# SQLAlchemy models
Base = declarative_base()


class Settings(Base):
    __tablename__ = "harmonic_settings"

    setting_name = Column(String, primary_key=True)


class Company(Base):
    __tablename__ = "companies"

    created_at: Union[datetime, Column[datetime]] = Column(
        DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False
    )
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    company_id = Column(Integer, nullable=True)
    city = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    website_url = Column(String, nullable=True)
    website_text = Column(Text, nullable=True)
