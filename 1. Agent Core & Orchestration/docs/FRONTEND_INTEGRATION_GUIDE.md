# 프론트 연동 가이드 (3번 백엔드 ↔ 4번 프론트 ↔ 1번 오케스트레이터)

> 대상: **3번(백엔드)**. 프론트(4번 `apps/web`)와의 계약을 맞추기 위해
> 백엔드에서 고쳐야 할 부분을 정리한다.
> 핵심 원칙: **응답을 직접 조립하지 말고, 1번이 제공하는 변환 함수 2개를 호출**한다.

## 0. 현재 문제 (왜 이 문서가 필요한가)

소켓 URL(`/ws/reading/{id}`)만 맞고, 양방향 메시지 계약이 어긋나 있다.
프론트는 모든 호출에 fallback mock이 있어 화면은 떠 보이지만 **실데이터가 흐르지 않는다.**

| 구분 | 프론트가 보내/기대 | 현재 3번 | 결과 |
|---|---|---|---|
| WS 송신 | 이벤트 **1개** `{type, sessionId, timestamp, payload}` | `{events:[...]}` 기대 | 이벤트 적재 0, focus 항상 100 |
| WS 응답 | `{type, payload:{nudgeLevel, nudgeMessage, focusScore}}` | `{focus_score, intervention_level,...}` flat | 프론트 `command.type` undefined |
| `/start` body | `{articleId, userId}` | `{user_id, document_id}` | 422 |
| `/start` 응답 | `{sessionId, article, wsEndpoint}` | `{session_id, message}` | article/ws 못 받음 |
| `/{id}/result` | `SessionResultResponse` | **없음** | 대시보드 못 그림 |

## 1. 1번이 제공하는 변환 함수 (이걸 호출만 하면 됨)

```python
from backend.app.api.frontend_contract import (
    to_intervention_command,   # state -> 프론트 InterventionCommand (WS ③→④)
    to_session_result,         # state -> 프론트 SessionResultResponse (REST 결과)
)
```

이 두 함수가 snake→camel, flat→`{type, payload}` 중첩, badge 문자열→객체배열,
없는 필드 파생까지 전부 처리한다. **3번은 응답 dict를 직접 만들 필요가 없다.**

## 2. WebSocket 수정 (`ws.py`)

### 2-1. 프론트는 이벤트를 1개씩 보낸다

```python
# 변경 전: event_payload.get("events", [])  ← 프론트는 events 키를 안 보냄
# 변경 후: 받은 메시지 자체가 이벤트 1개
front_event = json.loads(data)   # {type, sessionId, timestamp, payload:{...}}
```

### 2-2. 프론트 이벤트 → 오케스트레이터 reading_events 매핑

오케스트레이터 `ReadingEvent` 스키마: `{type, timestamp_ms, position?, duration_ms?, metadata?}`
프론트 → 내부 필드 변환:

| 프론트 | 내부 reading_events | 비고 |
|---|---|---|
| `type: scroll` | `type: scroll` | 그대로 |
| `type: dwell` | `type: pause` | 체류 = pause |
| `type: blur` | `type: blur` | 그대로 |
| `type: focus` | `type: focus` | 그대로 |
| `timestamp` | `timestamp_ms` | 그대로(ms) |
| `payload.progress` (0~100) | `position` (0~1) | `/100` |
| `payload.dwellMs` | `duration_ms` | 그대로 |

```python
_TYPE_MAP = {"scroll": "scroll", "dwell": "pause", "blur": "blur", "focus": "focus"}

def to_reading_event(front_event: dict) -> dict:
    p = front_event.get("payload", {})
    ev = {
        "type": _TYPE_MAP.get(front_event.get("type"), "click"),
        "timestamp_ms": int(front_event.get("timestamp", 0)),
    }
    if p.get("progress") is not None:
        ev["position"] = p["progress"] / 100
    if p.get("dwellMs") is not None:
        ev["duration_ms"] = int(p["dwellMs"])
    return ev
```

### 2-3. 응답은 변환 함수로

Redis에 누적한 이벤트로 state를 만들고, **`to_intervention_command(state)`를 그대로 전송**한다.

```python
from backend.app.orchestrator.state import create_initial_state
from backend.app.agents.cognitive_care_client import run_cognitive_care
from backend.app.orchestrator.routing import decide_intervention
from backend.app.api.frontend_contract import to_intervention_command

# all_events = Redis에서 가져온 reading_events
state = create_initial_state(session_id=session_id, user_id="...", document_id="...", raw_text="")
state["reading_events"] = all_events
run_cognitive_care(state)      # focus_score 계산 (real 토글 시 3번 모듈)
decide_intervention(state)     # focus → intervention 결정 (1번 routing)

await websocket.send_text(json.dumps(to_intervention_command(state), ensure_ascii=False))
```

> 실시간 WS에선 전체 폐루프(`run_reading_session`)까지 돌릴 필요 없이
> `run_cognitive_care` + `decide_intervention`만 호출하면 충분하다(가볍고 빠름).

## 3. REST 수정 (`endpoints.py`)

### 3-1. `/api/session/start` — 프론트 계약에 맞춤

```python
class StartSessionRequest(BaseModel):
    articleId: str
    userId: str

class StartSessionResponse(BaseModel):
    sessionId: str
    article: dict          # {id, title, category, author, publishedAt, content[], difficulty}
    wsEndpoint: str        # ex) ws://host/ws/reading/{sessionId}

@router.post("/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest, ...):
    session_id = f"s_{uuid4().hex[:8]}"
    # ... DB 저장 (req.userId, req.articleId) ...
    return StartSessionResponse(
        sessionId=session_id,
        article=load_article(req.articleId),   # 2번 Content Reducer 출력 or mock
        wsEndpoint=f"ws://{host}/ws/reading/{session_id}",
    )
```

### 3-2. `/api/session/{id}/result` — 신규, 변환 함수 반환

```python
from backend.app.orchestrator.graph import run_reading_session
from backend.app.api.frontend_contract import to_session_result

@router.get("/{session_id}/result")
async def get_session_result(session_id: str, ...):
    state = build_state_from_db(session_id)   # raw_text, reading_events, quiz_result, profile
    final_state = run_reading_session(state)  # 전체 폐루프 1회
    return to_session_result(final_state)     # ← 프론트 SessionResultResponse 그대로
```

> 기존 `/finish`는 DB 플러시 용도로 유지하되, 프론트 대시보드는 `/result`를 쓴다.
> (또는 `/finish` 응답에 `to_session_result(final_state)`를 합쳐도 된다.)

## 4. 검증 체크리스트

- [ ] 프론트에서 스크롤/블러 시 WS로 `{type, payload}` 단건이 오고, 백엔드가 파싱한다.
- [ ] 집중 떨어뜨리면 WS 응답 `type:"nudge"`가 와서 NudgeController가 뜬다.
- [ ] `/start`에 `{articleId, userId}`로 호출 시 `article`, `wsEndpoint`가 온다.
- [ ] `/{id}/result`가 `literacyScore/scoreSeries/badges` 포함 JSON을 준다.
- [ ] 프론트 콘솔에 "falling back to mock" 경고가 더는 안 뜬다. ← 진짜 연동 신호

## 5. 참고

- 변환 함수 구현/규칙: `backend/app/agents/.../api/frontend_contract.py` 주석
- 프론트 계약 원본: `apps/web/src/lib/api.ts` (InterventionCommand, SessionResultResponse)
- focus 점수 캘리브레이션은 별도: `docs/CALIBRATION_REQUEST_COGNITIVE_CARE.md`
