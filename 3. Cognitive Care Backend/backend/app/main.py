import sys
import asyncio
import traceback
import os

# 로컬 .env 파일 환경변수 자동 로드
try:
    # __file__ is backend/app/main.py
    # os.path.dirname(__file__) is backend/app
    # os.path.dirname(...) is backend
    # os.path.dirname(...) is project root (where .env is)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
        print(f"[Startup] Loaded environment from local .env file: {env_path}")
    else:
        print(f"[Startup] .env file not found at {env_path}")
except Exception as e:
    print(f"[Startup] Failed to load .env: {e}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .api import ws, endpoints, extension_session, terms, users
from .core.db import engine, Base
from .models import models

# 단일 호스트 배포용: 빌드된 프론트엔드(dist) 위치
# main.py = <backend_root>/backend/app/main.py → 상위 3단계가 프로젝트 폴더
_FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend_dist",
)


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
    allow_credentials=False,
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
    # 프론트가 번들돼 있으면 SPA 진입점(index.html)을, 아니면 상태 JSON을 반환
    index_path = os.path.join(_FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
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


# ==============================
# 프론트엔드 정적 서빙 (단일 호스트 배포)
# ==============================
if os.path.isdir(_FRONTEND_DIR):
    _assets_dir = os.path.join(_FRONTEND_DIR, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """API/WS를 제외한 모든 경로는 SPA index.html로 폴백(클라이언트 라우팅)."""
        if full_path.startswith(("api/", "ws/")):
            return JSONResponse(status_code=404, content={"error": "Not Found", "path": "/" + full_path})
        candidate = os.path.join(_FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))

    print(f"[Startup] Serving frontend from {_FRONTEND_DIR}")
else:
    print(f"[Startup] Frontend dist not found at {_FRONTEND_DIR} (API-only mode)")
