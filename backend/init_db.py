from app.core.database import Base, engine
from app.models.user import User
import subprocess
import os

def init_db():
    """Initialize the database by creating tables and running migrations."""
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
    
    # Run migrations if alembic directory exists
    if os.path.exists("alembic"):
        print("Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running migrations: {result.stderr}")
            return False
        
        print(f"Migrations applied successfully: {result.stdout}")
    
    return True

if __name__ == "__main__":
    init_db() 