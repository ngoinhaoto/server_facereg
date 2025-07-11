import os
import sys
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from sqlalchemy_utils import database_exists, drop_database, create_database
from config.database import DATABASE_URL
from models.database import Base
from database.db import engine

def reset_database():
    print("Starting database reset process...")
   
    # Step 1: Drop the database if it exists
    if database_exists(DATABASE_URL):
        print(f"Dropping database: {DATABASE_URL}")
        drop_database(DATABASE_URL)
   
    # Step 2: Create a fresh database
    print(f"Creating new database: {DATABASE_URL}")
    create_database(DATABASE_URL)
   
    # Step 3: Enable pgvector extension and create tables
    print("Creating database tables...")
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()  # Make sure the extension is committed
        print("pgvector extension enabled successfully!")
        
    # Create all tables using SQLAlchemy
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
   
    # Step 4: Mark migrations as completed (optional)
    try:
        # This will mark the migrations as completed without running them
        alembic_result = subprocess.run(
            ["alembic", "stamp", "head"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )
       
        if alembic_result.returncode != 0:
            print("Warning: Could not mark migrations as completed:")
            print(alembic_result.stderr)
        else:
            print("Migrations marked as completed successfully!")
    except Exception as e:
        print(f"Warning: Could not mark migrations as completed: {str(e)}")
   
    # Step 5: Seed the database with sample data
    print("Seeding database with sample data...")
    try:
        from scripts.seed_db import create_sample_data
        create_sample_data()
        print("Database reset and seeding completed successfully!")
        return True
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        import sqlalchemy_utils
    except ImportError:
        print("Installing sqlalchemy-utils...")
        os.system("pip install sqlalchemy-utils")
        
    try:
        import pgvector
    except ImportError:
        print("Installing pgvector...")
        os.system("pip install pgvector")
   
    confirmation = input("⚠️  WARNING: This will DELETE all data in the database. Are you sure? (yes/no): ")
    if confirmation.lower() == "yes" or confirmation.lower() == "y":
        reset_database()
    else:
        print("Operation cancelled.")