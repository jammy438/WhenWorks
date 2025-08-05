from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.models.base import Base

# Database connection string
# Database URL format: postgresql+psycopg2://<username>:<password>@<host>:<port>/<database_name>
DATABASE_URL = "postgresql+psycopg2://postgres:H4HSnh8s@localhost:5433/whenworks"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)  # Fixed: use DATABASE_URL, not DATABASEURL

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
    # Since all models should inherit from the same Base, you only need to call this once
    Base.metadata.create_all(bind=engine)