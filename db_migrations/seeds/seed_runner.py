#!/usr/bin/env python3
import sys
import os

# Add backend to path and change to backend directory
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)

# Now imports should work (from backend directory context)
from backend.database import SessionLocal
from development_data import seed_development_database

def main():
    print("🌱 Seeding development database...")
    
    db = SessionLocal()
    try:
        result = seed_development_database(db)
        print(f"✅ Database seeding completed! Created {result['users']} users and {result['events']} events")
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        return 1
    finally:
        db.close()
    return 0

if __name__ == "__main__":
    exit(main())
