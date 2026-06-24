"""FastAPI 앱 시작점.

[골격: 6/20 / 실제 서버: 6/22 이후]

1번 역할이 전체 서버를 완성할 필요는 없지만, 오케스트레이터를 호출하는
최소 API는 여기서 마운트한다.

실행 (FastAPI 도입 후):
    uvicorn backend.app.main:app --reload
"""

from __future__ import annotations

# TODO(6/22): FastAPI 앱 생성 및 reading_session 라우터 등록.
#   from fastapi import FastAPI
#   from .api import reading_session
#   app = FastAPI(title="AI Literacy Care Agent")
#   app.include_router(reading_session.router, prefix="/api")

app = None  # placeholder — FastAPI 앱으로 교체 예정
