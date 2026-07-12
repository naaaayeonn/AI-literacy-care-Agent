"""
contracts.py — Content Reducer 에이전트 입출력 타입 정의 (M0)

모든 팀원이 이 파일의 타입을 기준으로 연결 작업을 수행한다.
변경 시 반드시 1번(Orchestrator)에 공지할 것.

chunk_id 규칙: chunk_{document_id}_{순번(2자리 zero-padding)}
  예시: chunk_doc001_01, chunk_doc001_02
"""
from __future__ import annotations

from typing import Literal, NotRequired, TypedDict


# ---------------------------------------------------------------------------
# 용어풀이 (RAG 출력)
# ---------------------------------------------------------------------------

class TermDict(TypedDict):
    term: str                          # 원문 용어
    definition: str                    # 신뢰 출처 기반 풀이
    source: str                        # 출처 (예: "표준국어대사전")
    faithfulness_score: NotRequired[float]  # 0~1, 높을수록 출처에 충실
    chunk_id: str                      # 해당 용어가 등장한 chunk
    _meta: NotRequired[dict]           # 2번 팀 디버그 추적 필드 {tried: [], errors: {}}


# ---------------------------------------------------------------------------
# 퀴즈 (Quiz Generator 출력)
# ---------------------------------------------------------------------------

class QuizDict(TypedDict):
    quizId: str
    type: Literal["ox"]
    statement: str
    answer: bool
    explanation: str
    sourceChunkId: str


# ---------------------------------------------------------------------------
# 청크 (Semantic Chunker 출력)
# ---------------------------------------------------------------------------

class ChunkDict(TypedDict):
    chunk_id: str
    original_text: str
    restructured_text: NotRequired[str]   # LLM 재구성 결과 (향후 폐기 예정)
    summary: NotRequired[str]             # 문단별 1문장 요약
    difficulty: float                      # 0~100 (높을수록 어려움)
    terms: NotRequired[list[TermDict]]
    char_start: int                        # 원문에서의 시작 위치 (프론트 하이라이트용)
    char_end: int                          # 원문에서의 종료 위치


# ---------------------------------------------------------------------------
# Content Reducer 요청 / 응답
# ---------------------------------------------------------------------------

class ContentReducerRequest(TypedDict):
    session_id: str
    raw_text: str
    user_literacy_level: int       # 1(초급) ~ 5(전문가)
    target_domain: NotRequired[str]
    profile: NotRequired[dict]


class ContentReducerResponse(TypedDict):
    session_id: str
    readability_score: float       # 0~100, 높을수록 읽기 쉬움
    difficulty_score: float        # 0~100, 높을수록 어려움 (= 100 - readability)
    chunks: list[ChunkDict]
    simplified_text: str           # 전체 재구성 텍스트 (프론트 전체보기용)
    terms: list[TermDict]          # 세션 전체 용어 목록 (중복 제거)


# ---------------------------------------------------------------------------
# 퀴즈 생성 요청 (Cognitive Care → Content Reducer)
# ---------------------------------------------------------------------------

class QuizGenerationRequest(TypedDict):
    session_id: str
    chunk_id: str
    context: str                   # 해당 chunk의 restructured_text
    user_literacy_level: NotRequired[int]


# ---------------------------------------------------------------------------
# 1번 Orchestrator와 공유하는 Shared State
# (1번 ARCHITECTURE_1.md의 ReadingSessionState와 호환)
# ---------------------------------------------------------------------------

class ReadingSessionState(TypedDict):
    session_id: str
    user_id: str
    document_id: str
    raw_text: str

    # --- 2번이 채우는 필드 ---
    profile: dict
    chunks: NotRequired[list[ChunkDict]]
    simplified_text: NotRequired[str]
    terms: NotRequired[list[TermDict]]
    difficulty_score: NotRequired[float]
    readability_score: NotRequired[float]

    # --- 3번이 채우는 필드 (2번은 읽기만) ---
    reading_events: NotRequired[list[dict]]
    focus_score: NotRequired[float]
    engagement_score: NotRequired[float]
    intervention_needed: NotRequired[bool]
    intervention_level: NotRequired[Literal["none", "soft", "medium", "hard"]]

    # --- 2번이 3번 트리거 수신 후 생성하는 퀴즈 ---
    quiz: NotRequired[QuizDict]

    # --- 1번이 채우는 필드 ---
    quiz_result: NotRequired[dict]
    comprehension_score: NotRequired[float]
    literacy_score: NotRequired[float]
    score_breakdown: NotRequired[dict]
    reward: NotRequired[dict]
    updated_profile: NotRequired[dict]

    # --- 공통 (모든 에이전트가 누적) ---
    trace: list[dict]
    errors: list[dict]
