import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Database")

Base = declarative_base()

def get_engine():
    """Initializes database engine with PostgreSQL and graceful SQLite fallback."""
    pg_url = Config.DATABASE_URL
    try:
        if pg_url.startswith("postgresql"):
            test_engine = create_engine(pg_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            # Test connection
            with test_engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL database.")
            return test_engine
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite local database.")
    
    # SQLite Fallback for local development if PostgreSQL is offline
    sqlite_path = Config.SQLITE_FALLBACK_PATH
    sqlite_url = f"sqlite:///{sqlite_path}"
    logger.info(f"Using SQLite database at: {sqlite_url}")
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency session generator for route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables defined in models."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
