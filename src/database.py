import os
import ssl  
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Pull the DB connection string from the environment variable
RAW_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:secretpassword@db:5432/chatdb")

# Auto-adjust driver prefix formatting for asyncpg compliance
if RAW_DB_URL.startswith("postgresql://"):
    DATABASE_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = RAW_DB_URL

# Handle SSL connection arguments using a real SSL Context object
if "localhost" in DATABASE_URL or "@db:" in DATABASE_URL:
    connect_args = {}
else:
    # Production Cloud database setup (Railway)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Safe fallback for cloud managed DBs
    
    connect_args = {"ssl": ssl_context}  # <-- Injects the context object directly

# Create the async engine
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass