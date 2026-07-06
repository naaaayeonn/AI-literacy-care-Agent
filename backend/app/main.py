import sys
import asyncio
import traceback

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .api import ws, endpoints, extension_session, terms, users
from .core.db import engine, Base
from .models import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB/Redis & Create Tables
    print("Starting up AI Literacy Care Backend...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[Startup] Database tables created successfully.")
    except Exception as e:
        print(f"[Warning] DB Connection Failed (Docker/PostgreSQL Offline). Continuing in Demo Mode: {e}")
    
    # Redis 연결 확인
    try:
        from .core.redis import get_redis
        redis_client = await get_redis()
        await redis_client.ping()
        print("[Startup] Redis connection OK.")
        await redis_client.aclose()
    except Exception as e:
        print(f"[Startup] Redis connection warning: {e}")
        print("[Startup] Continuing without Redis (WebSocket caching will use InMemoryFallback).")
    
    yield
    
    # Shutdown: Close connections
    print("Shutting down AI Literacy Care Backend...")
    try:
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="AI Literacy Care API",
    description="AI 리터러시 케어 - 실시간 읽기 행동 분석 및 문해력 향상 플랫폼",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
# Global Exception Handlers (6/27~6/28)
# ==============================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """모든 미처리 예외를 잡아서 500 JSON 응답으로 변환."""
    tb = traceback.format_exc()
    print(f"[ERROR] Unhandled exception on {request.method} {request.url}:\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "path": str(request.url),
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "path": str(request.url)}
    )


# Register routers
app.include_router(ws.router)
app.include_router(endpoints.router)
app.include_router(extension_session.router)
app.include_router(terms.router)
app.include_router(users.router)


@app.get("/")
async def root():
    return {"message": "AI Literacy Care Backend is running!", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트."""
    health = {"status": "ok", "db": "unknown", "redis": "unknown"}
    
    try:
        from .core.db import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(models.User.__table__.select().limit(1))
        health["db"] = "connected"
    except Exception as e:
        health["db"] = f"error: {str(e)[:50]}"
    
    try:
        from .core.redis import get_redis
        redis_client = await get_redis()
        await redis_client.ping()
        health["redis"] = "connected"
        await redis_client.aclose()
    except Exception as e:
        health["redis"] = f"error: {str(e)[:50]}"
    
    return health
