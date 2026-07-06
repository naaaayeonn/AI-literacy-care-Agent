from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os

# PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:password@localhost:5432/literacy_care")

# PostgreSQL 연결 검증 여부 플래그
_db_verified = False

if DATABASE_URL.startswith("postgresql"):
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        connect_args={"connect_timeout": 3} # psycopg 타임아웃 옵션은 connect_timeout 입니다.
    )
else:
    engine = create_async_engine("sqlite+aiosqlite:///./literacy_care.db", echo=False)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    global engine, AsyncSessionLocal, _db_verified
    
    # 데이터베이스 연결 사전 확인 및 SQLite 폴백 전환 (컨텍스트 누수 방어)
    if "postgresql" in str(engine.url) and not _db_verified:
        try:
            # 3초 타임아웃 연결 테스트 실행
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            _db_verified = True
            print("[DB] PostgreSQL connection verified.")
        except Exception as e:
            print(f"[DB] PostgreSQL connection failed ({e}). Switching to SQLite...")
            engine = create_async_engine("sqlite+aiosqlite:///./literacy_care.db", echo=False)
            AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            _db_verified = True
            
    # 검증된 안전한 세션 생성
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


