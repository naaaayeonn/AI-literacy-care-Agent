"""테스트용 시드 데이터 (6/29 M1 구현)

사용법:
    python -m app.db.seeds
"""

import asyncio
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# backend 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.db import engine, Base, AsyncSessionLocal
from app.models.models import User, ReadingSession, LiteracyProfile


SEED_USERS = [
    {"id": "user-001"},
    {"id": "user-002"},
    {"id": "test-user"},
]

SEED_PROFILES = [
    {
        "user_id": "user-001",
        "total_sessions": 3,
        "avg_literacy_score": 72.5,
        "avg_comprehension": 78.0,
        "avg_engagement": 65.0,
        "current_level": 2,
        "total_xp": 185,
        "weaknesses": {"focus": 65.0},
        "strengths": {"comprehension": 78.0},
        "trend": "improving",
    },
]


async def seed_database():
    """DB 시드 데이터 삽입."""
    global engine, AsyncSessionLocal
    print("[Seed] Creating tables...")
    
    # DB 연결 확인 및 SQLite 전환용 context
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[Seed] PostgreSQL tables creation failed: {e}")
        print("[Seed] Falling back to SQLite for local seeding...")
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        engine = create_async_engine("sqlite+aiosqlite:///./literacy_care.db", echo=True)
        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 사용자 생성
        for user_data in SEED_USERS:
            from sqlalchemy.future import select
            result = await db.execute(select(User).filter(User.id == user_data["id"]))
            if not result.scalars().first():
                db.add(User(**user_data))
                print(f"[Seed] Created user: {user_data['id']}")
        
        await db.commit()
        
        # 프로필 생성
        for profile_data in SEED_PROFILES:
            from sqlalchemy.future import select
            result = await db.execute(
                select(LiteracyProfile).filter(LiteracyProfile.user_id == profile_data["user_id"])
            )
            if not result.scalars().first():
                db.add(LiteracyProfile(**profile_data))
                print(f"[Seed] Created profile for: {profile_data['user_id']}")
        
        await db.commit()
    
    print("[Seed] Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
