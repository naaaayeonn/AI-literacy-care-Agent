from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
import subprocess
import sys

try:
    import aiosqlite
except ImportError:
    print("[DB] aiosqlite not found. Installing dynamically...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiosqlite"])
        print("[DB] aiosqlite installed successfully.")
    except Exception as e:
        print(f"[DB] Dynamic install of aiosqlite failed: {e}")

# PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production Mode (Render): Connect to PostgreSQL. Do not fall back to SQLite.
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"connect_timeout": 15}
    )
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    _db_verified = True
else:
    # Development Mode (Local): Default to SQLite
    engine = create_async_engine("sqlite+aiosqlite:///./literacy_care.db", echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    _db_verified = True

Base = declarative_base()

async def get_db():
    global engine, AsyncSessionLocal, _db_verified
    
    # SQLite의 경우 테이블들을 자동으로 즉각 생성하도록 보장
    if not DATABASE_URL and _db_verified:
        # 첫 호출 시에만 테이블 생성
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise



