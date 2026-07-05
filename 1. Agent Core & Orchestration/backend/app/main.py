"""FastAPI entrypoint for the AI Literacy Care Agent backend."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.extension_session import router as extension_session_router
from backend.app.api.reading_session import router as reading_session_router


def _load_dotenv() -> None:
    """저장소 .env를 최선 노력으로 로드(python-dotenv 의존 없이).

    이미 설정된 환경변수는 덮어쓰지 않는다. GEMINI_API_KEY·구현 토글 등을
    앱 프로세스에 주입해 content_reducer 브릿지가 Gemini를 쓸 수 있게 한다.

    ⚠️ import 시점이 아니라 **서버 startup(lifespan)** 에서만 호출한다.
    import 부작용으로 os.environ을 바꾸면 pytest 수집 단계에서 토글이 오염돼
    스텁 기반 M0/M1 테스트가 깨진다(테스트는 bare TestClient라 lifespan 미발동).
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("\"'")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _load_dotenv()  # 실서버(uvicorn) 기동 시에만 .env 주입
    yield


app = FastAPI(title="AI Literacy Care Agent", version="0.1.0", lifespan=lifespan)

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
