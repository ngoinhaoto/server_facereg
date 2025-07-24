from sqlalchemy import MetaData, create_engine
from sqlalchemy_schemadisplay import create_schema_graph
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Construct the DATABASE_URL from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Generate the schema graph
graph = create_schema_graph(
    metadata=MetaData(),
    engine=engine,          # Pass the engine here
    show_datatypes=False,   # Hide datatypes to keep the diagram clean
    show_indexes=False,     # Hide indexes for simplicity
    rankdir='LR',           # Arrange the diagram from left to right
    concentrate=False       # Avoid merging relation lines
)

# Save the schema diagram as a PNG file
graph.write_png('dbschema.png')
print("Database schema diagram saved as 'dbschema.png'")