import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Pull the DB connection string from the docker environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:secretpassword@localhost:5432/chatdb")

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session factory to handle short-lived database queries
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Base class used to declare database structure profiles
class Base(DeclarativeBase):
    pass