import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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
    except Exception as e:
        print(f"⚠️ DB 연결 실패 (Docker 미실행 등). 데모 모드로 계속 진행합니다: {e}")
    yield
    # Shutdown: Close connections
    print("Shutting down AI Literacy Care Backend...")

app = FastAPI(title="AI Literacy Care API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ws.router)
app.include_router(endpoints.router)
app.include_router(extension_session.router)
app.include_router(terms.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "AI Literacy Care Backend is running!"}
