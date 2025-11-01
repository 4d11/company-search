#!/usr/bin/env python3
"""
Standalone script to seed the database with companies, locations, industries, and target markets.
Run this separately from the application.
"""

import csv
import json
import random
from pathlib import Path

from backend.db.database import (
    Company,
    FundingStage,
    Industry,
    Location,
    SessionLocal,
    Settings,
    TargetMarket,
)
from backend.es.client import es_client
from backend.es.index import create_company_index
from backend.es.operations import bulk_index_companies
from backend.db.database import Base, engine
from backend.llm.attribute_extractor import extract_company_attributes
from backend.llm.extraction_cache import extraction_cache
from backend.settings import settings

def seed_database():
    """
    Seed the database with locations, industries, target markets, and companies.
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()


    try:
        print("=" * 60)
        print("DATABASE SEEDING SCRIPT")
        print("=" * 60)

        # Check if already seeded
        if db.query(Settings).get("seeded"):
            response = input("Database already seeded. Re-seed? (yes/no): ")
            if response.lower() != "yes":
                print("Aborted.")
                return

        # Load seed data for industries and target markets
        seed_data_path = Path(__file__).parent / "backend" / "db" / "seed_data.json"
        with open(seed_data_path, 'r') as f:
            seed_data = json.load(f)

        # Extract unique locations from CSV first
        print("\nExtracting unique locations from CSV...")
        csv_path = Path(__file__).parent / "backend" / "db" / "B2B_SaaS_2021-2022.csv"
        unique_cities = set()

        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Skip the first line (title line)
                next(file)
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    city = row.get('City', '').strip()
                    if city:
                        unique_cities.add(city)

        # Seed locations from CSV
        print("Seeding locations from CSV...")
        location_map = {}
        for city in sorted(unique_cities):
            # Check if location already exists
            existing = db.query(Location).filter(Location.city == city).first()
            if existing:
                location_map[city] = existing.id
            else:
                location = Location(city=city)
                db.add(location)
                db.flush()
                location_map[city] = location.id
        db.commit()
        print(f"✓ Seeded {len(location_map)} locations from CSV")

        # Seed industries
        print("Seeding industries...")
        industry_map = {}
        for industry_name in seed_data['industries']:
            existing = db.query(Industry).filter(Industry.name == industry_name).first()
            if existing:
                industry_map[industry_name] = existing.id
            else:
                industry = Industry(name=industry_name)
                db.add(industry)
                db.flush()
                industry_map[industry_name] = industry.id
        db.commit()
        print(f"✓ Seeded {len(industry_map)} industries")

        # Seed target markets
        print("Seeding target markets...")
        target_market_map = {}
        for market_name in seed_data['target_markets']:
            existing = db.query(TargetMarket).filter(TargetMarket.name == market_name).first()
            if existing:
                target_market_map[market_name] = existing.id
            else:
                market = TargetMarket(name=market_name)
                db.add(market)
                db.flush()
                target_market_map[market_name] = market.id
        db.commit()
        print(f"✓ Seeded {len(target_market_map)} target markets")

        # Seed funding stages
        print("Seeding funding stages...")
        funding_stage_map = {}
        for stage_data in seed_data['funding_stages']:
            existing = db.query(FundingStage).filter(FundingStage.name == stage_data['name']).first()
            if existing:
                funding_stage_map[stage_data['name']] = existing.id
            else:
                stage = FundingStage(name=stage_data['name'], order_index=stage_data['order_index'])
                db.add(stage)
                db.flush()
                funding_stage_map[stage_data['name']] = stage.id
        db.commit()
        print(f"✓ Seeded {len(funding_stage_map)} funding stages")

        # Load companies from CSV (already opened above for location extraction)
        if csv_path.exists():
            print("\nLoading companies from CSV...")
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Skip the first line (title line)
                next(file)
                csv_reader = csv.DictReader(file)

                companies = []
                stage_names = list(funding_stage_map.keys())

                # Funding ranges for random assignment
                funding_ranges = {
                    "Stealth": (0, 100000),
                    "Pre-Seed": (50000, 500000),
                    "Seed": (500000, 3000000),
                    "Series A": (3000000, 15000000),
                    "Series B": (15000000, 50000000),
                    "Series C": (50000000, 150000000),
                    "Series D+": (150000000, 500000000),
                    "Growth": (100000000, 1000000000),
                    "Public": (500000000, 5000000000)
                }

                # Show cache stats if enabled
                if settings.use_llm_cache:
                    cache_stats = extraction_cache.stats()
                    print(f"LLM cache enabled: {cache_stats['cached_entries']} entries cached")

                print("Extracting attributes using LLM...")
                for idx, row in enumerate(csv_reader, 1):
                    company_name = row.get('Company Name', '')
                    description = row.get('Description', '')
                    website_text = row.get('Website Text', '')
                    city = row.get('City', '')

                    # Extract location, industries, and target markets using LLM
                    print(f"  [{idx}] Processing {company_name}...")
                    extracted = extract_company_attributes(
                        company_name=company_name,
                        description=description,
                        website_text=website_text,
                        db=db
                    )

                    # Map extracted location to ID, with fallbacks
                    location_id = None
                    if not location_id and city in location_map:
                        location_id = location_map.get(city)
                    if not location_id and extracted.get("location"):
                        location_id = location_map.get(extracted["location"])
                    if not location_id:
                        location_id = random.choice(list(location_map.values()))

                    # Generate random company metrics (not extracted by LLM)
                    employee_count = random.choice([5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000])
                    stage_name = random.choice(stage_names)
                    funding_stage_id = funding_stage_map[stage_name]
                    min_funding, max_funding = funding_ranges.get(stage_name, (0, 1000000))
                    funding_amount = random.randint(min_funding, max_funding)

                    company = Company(
                        company_name=company_name,
                        company_id=int(row.get('Company ID', 0)) if row.get('Company ID', '').isdigit() else None,
                        city=city,
                        description=description,
                        website_url=row.get('Website URL', ''),
                        website_text=website_text,
                        location_id=location_id,
                        funding_stage_id=funding_stage_id,
                        employee_count=employee_count,
                        funding_amount=funding_amount,
                    )
                    companies.append(company)

                    # Store extracted attributes for later assignment
                    company._extracted_industries = extracted.get("industries") or []
                    company._extracted_markets = extracted.get("target_markets") or []

                db.bulk_save_objects(companies)
                db.commit()
                print(f"✓ Loaded {len(companies)} companies from CSV")

            # Assign industries and target markets using LLM-extracted values
            print("\nAssigning industries and target markets from LLM extraction...")
            for idx, company in enumerate(companies):
                # Get the corresponding DB company (they're in the same order)
                db_company = db.query(Company).filter(Company.company_name == company.company_name).first()
                if not db_company:
                    continue

                # Assign LLM-extracted industries
                extracted_industries = getattr(company, '_extracted_industries', [])
                if extracted_industries:
                    for industry_name in extracted_industries:
                        industry_id = industry_map.get(industry_name)
                        if industry_id:
                            industry = db.query(Industry).get(industry_id)
                            if industry and industry not in db_company.industries:
                                db_company.industries.append(industry)
                else:
                    # Fallback to random if LLM didn't extract any
                    num_industries = random.randint(1, 2)
                    selected_industries = random.sample(list(industry_map.values()), num_industries)
                    for industry_id in selected_industries:
                        industry = db.query(Industry).get(industry_id)
                        if industry not in db_company.industries:
                            db_company.industries.append(industry)

                # Assign LLM-extracted target markets
                extracted_markets = getattr(company, '_extracted_markets', [])
                if extracted_markets:
                    for market_name in extracted_markets:
                        market_id = target_market_map.get(market_name)
                        if market_id:
                            market = db.query(TargetMarket).get(market_id)
                            if market and market not in db_company.target_markets:
                                db_company.target_markets.append(market)
                else:
                    # Fallback to random if LLM didn't extract any
                    num_markets = random.randint(1, 2)
                    selected_markets = random.sample(list(target_market_map.values()), num_markets)
                    for market_id in selected_markets:
                        market = db.query(TargetMarket).get(market_id)
                        if market not in db_company.target_markets:
                            db_company.target_markets.append(market)

            db.commit()
            print("✓ Completed industry and target market assignments")

            # Index companies into Elasticsearch
            print("\nIndexing into Elasticsearch...")
            print("Creating Elasticsearch index...")
            create_company_index(es_client)

            # Fetch companies with relationships for indexing
            db_companies = db.query(Company).all()
            print(f"Indexing {len(db_companies)} companies into Elasticsearch...")
            bulk_index_companies(es_client, db_companies)

            # Mark as seeded
            if not db.query(Settings).get("seeded"):
                db.add(Settings(setting_name="seeded"))
            db.commit()

            print("\n" + "=" * 60)
            print("✓ Database seeding completed successfully!")
            print("=" * 60)

        else:
            print(f"\n✗ CSV file not found at {csv_path}")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
