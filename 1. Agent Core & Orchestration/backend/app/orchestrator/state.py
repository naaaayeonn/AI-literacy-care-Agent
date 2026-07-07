"""Shared State 스키마 — 모든 에이전트가 공유하는 세션 상태.

1번 역할에서 가장 먼저 확정해야 하는 파일이다. 팀원(2~5번)은 이 state의
입력 필드와 출력 필드를 기준으로 자기 모듈을 구현한다.

설계 원칙
- TypedDict 사용: LangGraph StateGraph가 dict 기반 state를 그대로 받으며,
  Pydantic 모델보다 직렬화/부분 갱신이 단순하다. (API 경계 검증은 별도로
  contracts.py / Pydantic 요청 모델에서 담당)
- `total=False`(= NotRequired)로 선택 필드를 구분: 세션 시작 시점에는 비어
  있고, 각 에이전트가 단계적으로 채운다.
- 점수는 모두 0~100으로 정규화한다.

필드 소유권 (누가 읽고 쓰는가)
- content_reducer (2번): chunks, simplified_text, terms, difficulty_score  [쓰기]
- cognitive_care  (3번): reading_events[읽기], focus/engagement/intervention_* [쓰기]
- score_engine    (1번): comprehension_score, literacy_score, score_breakdown [쓰기]
- reward          (4번): reward                                              [쓰기]
- literacy_profile(5번): updated_profile                                     [쓰기]
- qa_eval         (6번): trace[읽기], generated outputs[읽기]                 [읽기]

상세 표는 docs/SHARED_STATE.md 참고 (6/21 작성 예정).
"""

from __future__ import annotations

from typing import Literal, TypedDict

# NotRequired는 3.11+ typing 정식 지원. 본 환경(3.13)에서 그대로 사용한다.
from typing import NotRequired

InterventionLevel = Literal["none", "soft", "medium", "hard"]
InterventionType = Literal["none", "highlight", "nudge", "quiz"]
ReadingEventType = Literal["scroll", "pause", "blur", "focus", "click"]


class ReadingEvent(TypedDict):
    """프론트(4번) → 백엔드(3번)로 들어오는 단일 읽기 행동 이벤트.

    - position: 스크롤 위치 비율 0.0~1.0 으로 통일
    - timestamp_ms: 세션 시작 기준 ms (이벤트 간 기준 통일 필요)
    """

    type: ReadingEventType
    timestamp_ms: int
    position: NotRequired[float]
    duration_ms: NotRequired[int]
    metadata: NotRequired[dict]


class QuizResult(TypedDict):
    """사용자가 푼 퀴즈 결과 (이해도 계산 입력)."""

    quiz_id: str
    correct_count: int
    total_count: int
    answers: list[dict]


class ScoreBreakdown(TypedDict):
    """Literacy Score 계산 근거. 점수가 왜 그렇게 나왔는지 설명한다."""

    comprehension_score: float
    engagement_score: float
    difficulty_score: float
    cross_validation_penalty: float
    penalty_breakdown: NotRequired[dict]
    reason: NotRequired[str]


class TraceEntry(TypedDict):
    """단계별 실행 로그. QA(6번)와 디버깅·발표 근거로 사용."""

    step: str
    status: Literal["success", "fallback", "error"]
    latency_ms: NotRequired[int]
    detail: NotRequired[dict]


class QualityWarning(TypedDict):
    """Self-Correction 검토에서 감지한 결과 품질 이상.

    사용자 흐름을 막지 않는 경고 신호다. QA(6번)와 발표용 '검증 가능한
    시스템' 근거, 디버깅에 사용한다.
    """

    code: str
    severity: Literal["info", "warning", "critical"]
    message: str
    field: NotRequired[str]
    detail: NotRequired[dict]


class InterventionCommand(TypedDict):
    """Frontend-renderable intervention command."""

    level: InterventionLevel
    type: InterventionType
    message: str
    target_chunk_id: NotRequired[str]
    reason: NotRequired[str]


class ReadingSessionState(TypedDict):
    """한 읽기 세션 전체의 공유 상태.

    create_state → content_reducer → cognitive_care → routing
    → score_engine → reward → profile_update → final_result
    흐름을 따라 필드가 점진적으로 채워진다.
    """

    # --- 세션 식별 (필수, 시작 시 주어짐) ---
    session_id: str
    user_id: str
    document_id: str
    raw_text: str
    profile: dict  # 이전 세션 누적 프로필 (없으면 빈 dict)

    # --- 2번 Content Reducer 산출 ---
    chunks: NotRequired[list[dict]]
    simplified_text: NotRequired[str]
    terms: NotRequired[list[dict]]
    difficulty_score: NotRequired[float]

    # --- 3번 Cognitive Care 산출 ---
    reading_events: list[ReadingEvent]
    focus_score: NotRequired[float]
    engagement_score: NotRequired[float]
    intervention_needed: NotRequired[bool]
    intervention_level: NotRequired[InterventionLevel]
    intervention_message: NotRequired[str]
    intervention: NotRequired[InterventionCommand]

    # --- 퀴즈 / 1번 Score Engine 산출 ---
    quiz_result: NotRequired[QuizResult]
    comprehension_score: NotRequired[float]
    literacy_score: NotRequired[float]
    score_breakdown: NotRequired[ScoreBreakdown]

    # --- 4번 Reward / 5번 Profile 산출 ---
    reward: NotRequired[dict]
    updated_profile: NotRequired[dict]

    # --- 공통 로깅 ---
    trace: list[TraceEntry]
    errors: list[dict]
    warnings: list[QualityWarning]  # Self-Correction 검토 결과


def create_initial_state(
    *,
    session_id: str,
    user_id: str,
    document_id: str,
    raw_text: str,
    profile: dict | None = None,
) -> ReadingSessionState:
    """세션 시작 시 빈 상태를 생성한다.

    TODO(6/22): orchestrator graph 진입점에서 이 함수를 호출하도록 연결.
    """
    return ReadingSessionState(
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
        raw_text=raw_text,
        profile=profile or {},
        reading_events=[],
        trace=[],
        errors=[],
        warnings=[],
    )
