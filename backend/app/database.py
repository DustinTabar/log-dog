from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# The database URL. For now a local SQLite file called logdog.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./logdog.db"

# The engine is the core connection to the database.
# connect_args is a SQLite-specific setting we need for FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# A session is how you talk to the DB in a single request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is what our model classes will inherit from.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()