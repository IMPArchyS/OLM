import os
from sqlmodel import Session, SQLModel, create_engine

DB_DRIVER = os.getenv("DB_DRIVER", "postgresql")
DB_HOST = os.getenv("DB_HOST", "db")  # Change to "db" for Docker
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "imp")
DB_PASSWORD = os.getenv("DB_PASSWORD", "imp")
DB_NAME = os.getenv("DB_NAME", "ovlcentral")

# Build the connection URL
DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Validates connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

def get_session():
    """Dependency function to get database session for FastAPI."""
    with Session(engine) as session:
        yield session