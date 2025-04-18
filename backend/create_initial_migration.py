#!/usr/bin/env python
import subprocess
import os

def create_initial_migration():
    print("Creating initial database migration...")
    
    # Generate migration
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "Create initial tables"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error creating migration: {result.stderr}")
        return False
    
    print(f"Migration created: {result.stdout}")
    return True

if __name__ == "__main__":
    create_initial_migration() 