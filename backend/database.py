from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base  # Only import Base from your base.py
from app.config.database_config import DATABASE_URL

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a session to interact with the database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables in the database (if they don't exist)
def init_db():
    # Import models to ensure they are registered with Base
    from app.models import user, events
    
    # Create all tables using the Base from base.py
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")