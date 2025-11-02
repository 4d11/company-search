# app/database.py
from datetime import datetime
from typing import Union

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from backend.settings import settings

engine = create_engine(
    settings.database_url,
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


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, unique=True, nullable=False, index=True)


class Industry(Base):
    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    synonyms = Column(ARRAY(String), nullable=True)  # Array of synonym strings for fuzzy matching


class TargetMarket(Base):
    __tablename__ = "target_markets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)


class BusinessModel(Base):
    __tablename__ = "business_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    synonyms = Column(ARRAY(String), nullable=True)  # Array of synonym strings for fuzzy matching


class RevenueModel(Base):
    __tablename__ = "revenue_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    synonyms = Column(ARRAY(String), nullable=True)  # Array of synonym strings for fuzzy matching


class FundingStage(Base):
    __tablename__ = "funding_stages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    order_index = Column(Integer, unique=True, nullable=False, index=True)


# Association table for Company-Industry many-to-many relationship
company_industries = Table(
    'company_industries',
    Base.metadata,
    Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True),
    Column('industry_id', Integer, ForeignKey('industries.id'), primary_key=True)
)


# Association table for Company-TargetMarket many-to-many relationship
company_target_markets = Table(
    'company_target_markets',
    Base.metadata,
    Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True),
    Column('target_market_id', Integer, ForeignKey('target_markets.id'), primary_key=True)
)


# Association table for Company-BusinessModel many-to-many relationship
company_business_models = Table(
    'company_business_models',
    Base.metadata,
    Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True),
    Column('business_model_id', Integer, ForeignKey('business_models.id'), primary_key=True)
)


# Association table for Company-RevenueModel many-to-many relationship
company_revenue_models = Table(
    'company_revenue_models',
    Base.metadata,
    Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True),
    Column('revenue_model_id', Integer, ForeignKey('revenue_models.id'), primary_key=True)
)


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

    # Company metrics
    employee_count = Column(Integer, nullable=True, index=True)
    funding_amount = Column(BigInteger, nullable=True, index=True)  # in USD

    # Foreign keys
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True, index=True)
    funding_stage_id = Column(Integer, ForeignKey('funding_stages.id'), nullable=True, index=True)

    # Relationships
    location = relationship("Location")
    funding_stage = relationship("FundingStage")
    industries = relationship("Industry", secondary=company_industries, backref="companies")
    target_markets = relationship("TargetMarket", secondary=company_target_markets, backref="companies")
    business_models = relationship("BusinessModel", secondary=company_business_models, backref="companies")
    revenue_models = relationship("RevenueModel", secondary=company_revenue_models, backref="companies")


class SearchLog(Base):
    """Log all search queries for analytics"""
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=True)  # Natural language query (can be empty if filters-only)
    filters_applied = Column(JSON, nullable=True)  # JSON of filters used
    result_count = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class LLMExtraction(Base):
    """Track LLM-discovered values that don't match existing database entries"""
    __tablename__ = "llm_extractions"

    id = Column(Integer, primary_key=True, index=True)
    raw_value = Column(String, nullable=False, index=True)  # e.g., "AI/ML", "PropTech"
    segment = Column(String, nullable=False, index=True)  # "industries", "target_markets", etc.
    matched_to = Column(String, nullable=True)  # Matched DB value if mapped
    count = Column(Integer, default=1, nullable=False)  # Frequency count
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = Column(String, default="pending", nullable=False, index=True)  # pending/approved/mapped/ignored
