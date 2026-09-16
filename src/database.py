import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# 1. Fetch the raw environment variable string
RAW_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:secretpassword@db:5432/chatdb")

# 2. FIX: Auto-adjust driver prefix formatting for asyncpg compliance if needed
if RAW_DB_URL.startswith("postgresql://"):
    DATABASE_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = RAW_DB_URL

# 3. Handle SSL connection arguments conditionally
if "localhost" in DATABASE_URL or "@db:" in DATABASE_URL:
    connect_args = {}
else:
    connect_args = {"ssl": "require"}

# 4. Create the async engine with correct protocols
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass