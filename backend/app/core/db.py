from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os

# PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:password@localhost:5432/literacy_care")

# 로컬 개발/테스트용 SQLite fallback을 적용합니다.
# 만약 환경 변수에 DATABASE_URL이 설정되어 있지 않거나 PostgreSQL 드라이버가 타임아웃이 나면 SQLite 파일 DB를 사용합니다.
if DATABASE_URL.startswith("postgresql"):
    # 로컬 연결 실패 대비 SQLite를 기본 fallback으로 설정할 수 있도록 처리
    # (실제 API 호출 시 첫 연결 단계에서 검증 또는 안전하게 SQLite 파일 생성)
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        connect_args={"timeout": 5} # 타임아웃을 짧게 5초로 설정
    )
else:
    engine = create_async_engine("sqlite+aiosqlite:///./literacy_care.db", echo=False)

# SQLite 사용 시를 대비해 데이터베이스 접속 에러 발생 시 SQLite로 자동 fallback 처리하는 세션 생성을 만듭니다.
# 또한 SQLite 커넥션 설정을 위한 분기도 여기에 들어갑니다.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    global engine, AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        # DB 연결 실패 시 SQLite로 긴급 전환
        if "postgresql" in str(engine.url):
            print(f"[DB] PostgreSQL connection failed ({e}). Falling back to SQLite...")
            engine = create_async_engine("sqlite+aiosqlite:///./literacy_care.db", echo=True)
            AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with AsyncSessionLocal() as session:
                yield session
        else:
            raise e

