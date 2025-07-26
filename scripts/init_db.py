# init_db.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from sqlalchemy_utils import database_exists, create_database
from config.database import DATABASE_URL
from models.database import Base # Assuming Base is defined here or imported
from database.db import engine # Assuming engine is imported

def init_db():
    print(f"Creating database: {DATABASE_URL}")
    # Only create if it doesn't exist, init_db shouldn't necessarily drop existing
    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)
    else:
        print(f"Database {DATABASE_URL} already exists. Skipping creation.")

    print("Enabling pgvector extension and creating tables...")
    with engine.connect() as connection: # Use 'connection' not 'conn' to avoid conflict with Base.metadata.create_all bind
        # Enable pgvector extension
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit() # Commit the extension creation
        print("pgvector extension enabled successfully!")

    # Create all tables using SQLAlchemy
    Base.metadata.create_all(bind=engine) # This should now work
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()