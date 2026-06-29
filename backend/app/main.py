import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api import ws, endpoints
from .core.db import engine, Base
from .models import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB/Redis & Create Tables
    print("Starting up AI Literacy Care Backend...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Close connections
    print("Shutting down AI Literacy Care Backend...")

app = FastAPI(title="AI Literacy Care API", lifespan=lifespan)

# Register routers
app.include_router(ws.router)
app.include_router(endpoints.router)

@app.get("/")
async def root():
    return {"message": "AI Literacy Care Backend is running!"}
