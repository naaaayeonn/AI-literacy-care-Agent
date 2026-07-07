# 3. Cognitive Care Backend 아키텍처

## 1. 문서 목적
본 문서는 AI 리터러시 케어 앱에서 **3번 역할 (Cognitive Care Backend)**의 시스템 구조와 핵심 모듈의 동작 방식을 정의합니다. 사용자의 실시간 읽기 행동 데이터를 수집하고 분석하여 집중도 점수를 계산하며, 오케스트레이터(1번)와 프론트엔드(4번)를 이어주는 중추적인 백엔드 서버 역할을 수행합니다.

## 2. 기술 스택
- **Web Framework**: FastAPI (Python 3.13+)
- **In-Memory Cache**: Redis (실시간 행동 데이터 버퍼링 및 TTL 관리)
- **Database**: PostgreSQL (최종 읽기 세션 및 이벤트 영구 저장)
- **Communication**: WebSocket (실시간 Nudge) / REST API (세션 시작, 최종 리포트)

## 3. 핵심 시스템 아키텍처

### 3.1. WebSocket 실시간 파이프라인 (`app/api/ws.py`)
프론트엔드로부터 `scroll`, `dwell`, `blur`, `focus` 등의 이벤트를 단건으로 수신하여 내부 규격(`pause`, `position`)으로 변환합니다. 수신된 이벤트는 Redis 리스트에 적재되며, 데이터가 들어올 때마다 Focus Score Engine을 가동합니다.

### 3.2. Focus Score Engine (`app/services/cognitive_care.py`)
Redis에 누적된 행동 데이터를 기반으로 사용자의 실시간 집중도를 계산합니다.
- **감점 요인**: 비정상적인 스크롤, 잦은 화면 이탈(Blur)
- **개입 결정 (Intervention)**: Focus Score 구간에 따라 `none`, `soft(highlight)`, `medium(nudge)`, `hard(quiz)` 단계로 분류하여 프론트엔드에 즉각적인 피드백을 전달합니다.

### 3.3. Orchestrator 통합 (`app/api/frontend_contract.py`)
1번 역할(오케스트레이터)이 정의한 Shared State 규격을 준수합니다. 백엔드 내부 연산 결과를 `ReadingSessionState`로 구성한 뒤, `to_intervention_command` 어댑터를 통해 프론트엔드가 렌더링할 수 있는 규격화된 JSON 명령으로 변환합니다.

### 3.4. REST API Endpoints (`app/api/endpoints.py`)
- **`POST /api/session/start`**: 새로운 읽기 세션을 발급하고 프론트엔드에 접속할 WebSocket Endpoint URL과 초기 아티클 데이터를 제공합니다.
- **`POST /api/session/{id}/finish`**: 세션이 종료되면 Redis에 있던 버퍼 데이터를 PostgreSQL로 Flush(저장)하고 오케스트레이터의 최종 계산 엔진을 가동합니다.
- **`GET /api/session/{id}/result`**: 최종 계산된 Literacy Score 및 각종 세션 결과를 프론트엔드 대시보드 뷰에 맞춰 반환합니다.

## 4. 데이터 흐름도 (Data Flow)
1. User reads article -> Frontend emits raw events via WebSocket.
2. Backend parses events -> Buffers in Redis.
3. Backend runs Cognitive Care Engine -> Computes Focus Score.
4. If score drops -> Determines Intervention (e.g., Nudge).
5. State passed to Orchestrator adapter -> Returns strict JSON format.
6. Frontend receives WS message -> Triggers UI Nudge.
7. User finishes -> POST `/finish` -> Flush to Postgres & Compute Final Literacy Score.
