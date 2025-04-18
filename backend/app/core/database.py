from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential
import os

from app.core.config import settings

# Get individual connection parameters from environment variables
PGHOST = os.environ.get("PGHOST")
PGUSER = os.environ.get("PGUSER")
PGPASSWORD = os.environ.get("PGPASSWORD")
PGDATABASE = os.environ.get("PGDATABASE")
PGPORT = os.environ.get("PGPORT", "5432")

# Construct the database URL manually
DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}?sslmode=require"

# Create engine with appropriate parameters for Neon PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enables reconnection on stale connections
    pool_recycle=300,    # Recycle connections every 5 minutes
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "keepalives": 1,        # Enable TCP keepalives
        "keepalives_idle": 60   # Seconds between keepalives
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def check_db_connection():
    """
    Attempts to connect to the database with retry logic.
    Exponential backoff between attempts.
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise 