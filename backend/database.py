from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.config.settings import get_settings

settings = get_settings()

# Create the SQLAlchemy engine
engine = create_engine(settings.database_url, echo=True)

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
    """
    Initialize database.
    Tables are now created/updated via Alembic migrations.
    Run: alembic upgrade head
    """
    print("Database initialization")
    print("Tables are managed by Alembic migrations")
    print("Run 'alembic upgrade head' to create/update tables")
    print("️Run 'alembic revision --autogenerate -m \"description\"' after model changes")
