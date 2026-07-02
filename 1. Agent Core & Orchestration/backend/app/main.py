"""FastAPI entrypoint for the AI Literacy Care Agent backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.extension_session import router as extension_session_router
from backend.app.api.reading_session import router as reading_session_router

app = FastAPI(title="AI Literacy Care Agent", version="0.1.0")

# CORS — 확장은 두 종류 Origin에서 호출한다:
#   1) content script: 사용자가 읽는 **임의 웹사이트** origin (chrome-extension 아님)
#   2) pdf 뷰어 페이지: chrome-extension://<id>
# 임의 사이트에서 읽으므로 dev/demo에선 모든 Origin 허용이 필요하다. 쿠키/인증을
# 쓰지 않으므로(allow_credentials=False) 위험이 낮다. 운영 강화 시에는 fetch를
# 서비스워커(chrome-extension origin)로 라우팅해 화이트리스트로 좁힌다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reading_session_router, prefix="/api")
app.include_router(extension_session_router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
