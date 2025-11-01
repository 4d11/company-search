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

        # Load seed data for locations, industries, and target markets
        seed_data_path = Path(__file__).parent / "backend" / "db" / "seed_data.json"
        with open(seed_data_path, 'r') as f:
            seed_data = json.load(f)

        # Seed locations
        print("\nSeeding locations...")
        location_map = {}
        for city in seed_data['locations']:
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
        print(f"✓ Seeded {len(location_map)} locations")

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

        # Load companies from CSV
        csv_path = Path(__file__).parent / "backend" / "db" / "B2B_SaaS_2021-2022.csv"

        if csv_path.exists():
            print("\nLoading companies from CSV...")
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Skip the first line (title line)
                next(file)
                csv_reader = csv.DictReader(file)

                companies = []
                stage_names = list(funding_stage_map.keys())

                for row in csv_reader:
                    # Randomly assign location, industries, and target markets for demo purposes
                    city = row.get('City', '')
                    location_id = location_map.get(city) if city in location_map else random.choice(list(location_map.values()))

                    # Generate random company metrics
                    employee_count = random.choice([5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000])
                    stage_name = random.choice(stage_names)
                    funding_stage_id = funding_stage_map[stage_name]

                    # Generate funding amount based on stage
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
                    min_funding, max_funding = funding_ranges.get(stage_name, (0, 1000000))
                    funding_amount = random.randint(min_funding, max_funding)

                    company = Company(
                        company_name=row.get('Company Name', ''),
                        company_id=int(row.get('Company ID', 0)) if row.get('Company ID', '').isdigit() else None,
                        city=city,
                        description=row.get('Description', ''),
                        website_url=row.get('Website URL', ''),
                        website_text=row.get('Website Text', ''),
                        location_id=location_id,
                        funding_stage_id=funding_stage_id,
                        employee_count=employee_count,
                        funding_amount=funding_amount,
                    )
                    companies.append(company)

                db.bulk_save_objects(companies)
                db.commit()
                print(f"✓ Loaded {len(companies)} companies from CSV")

            # Assign industries and target markets to companies
            print("\nAssigning industries and target markets...")
            db_companies = db.query(Company).all()
            for company in db_companies:
                # Randomly assign 1-3 industries
                num_industries = random.randint(1, 3)
                selected_industries = random.sample(list(industry_map.values()), num_industries)
                for industry_id in selected_industries:
                    industry = db.query(Industry).get(industry_id)
                    if industry not in company.industries:
                        company.industries.append(industry)

                # Randomly assign 1-2 target markets
                num_markets = random.randint(1, 2)
                selected_markets = random.sample(list(target_market_map.values()), num_markets)
                for market_id in selected_markets:
                    market = db.query(TargetMarket).get(market_id)
                    if market not in company.target_markets:
                        company.target_markets.append(market)

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
