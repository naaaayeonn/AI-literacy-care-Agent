"""Quiz result normalization and state integration.

두 계열이 공존한다.
- 기존 집계형(quiz_result / quiz_correct_rate): 프론트가 4지선다 세트 점수를 통째로
  보낼 때의 경로. 하위호환으로 유지.
- 신규 O/X 문항형(prebuild_quizzes / pick_quiz / submit_ox_quiz): 편지
  docs/FEEDBACK_TO_ROLE3_OX_QUIZ.md 스펙. 3번 vendored `quiz_service`의
  generate_ox_quiz·select_quiz_for_state를 1번이 배선한다(트리거 A/B·쿨다운·채점).
"""

from __future__ import annotations

import math

from backend.app.agents.real.quiz_service import (
    generate_ox_quiz,
    select_quiz_for_state,
)

from .state import QuizResult, ReadingSessionState


DEFAULT_QUIZ_ID = "quiz_unknown"

# --- O/X 트리거·쿨다운 상수 (편지 §5-3, routing determine_intervention과 컷오프 일치) ---
HARD_FOCUS_CUTOFF = 30.0   # (A) 집중 하락: focus < 30 → 재집중 + 측정
PROGRESS_FLOOR = 0.9       # (B) 본문 ~90% 읽으면 측정 보장
MIN_QUIZZES = 1            # 세션당 최소 보장(이해도 실측 보장)
MAX_QUIZZES = 3            # 도배 방지
COOLDOWN_MS = 25_000       # 마지막 퀴즈 후 재출제 금지 간격
FOCUS_RECOVERY = 15.0      # 정답 시 집중도 회복량
XP_PER_QUIZ = 10           # 정답 시 XP 리워드


def apply_quiz_result(state: ReadingSessionState, payload: dict) -> ReadingSessionState:
    """Normalize a quiz payload and attach it to shared state."""
    state["quiz_result"] = normalize_quiz_result(payload)
    return state


def normalize_quiz_result(payload: dict | None) -> QuizResult:
    """Return a safe QuizResult shape from frontend/API input."""
    payload = payload or {}
    total_count = _non_negative_int(payload.get("total_count", 0))
    correct_count = _non_negative_int(payload.get("correct_count", 0))
    correct_count = min(correct_count, total_count)

    answers = payload.get("answers", [])
    if not isinstance(answers, list):
        answers = []

    quiz_id = payload.get("quiz_id") or DEFAULT_QUIZ_ID

    return QuizResult(
        quiz_id=str(quiz_id),
        correct_count=correct_count,
        total_count=total_count,
        answers=answers,
    )


def quiz_correct_rate(quiz_result: QuizResult | dict | None, *, default: float = 0.7) -> float:
    """Calculate correct_count / total_count with a default for missing quiz data."""
    if not quiz_result:
        return default

    normalized = normalize_quiz_result(dict(quiz_result))
    if normalized["total_count"] <= 0:
        return default

    return normalized["correct_count"] / normalized["total_count"]


def _non_negative_int(value: object) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, number)


# ──────────────────────────────────────────────
# O/X 문항형 (편지 스펙) — 3번 quiz_service 배선
# ──────────────────────────────────────────────


def prebuild_quizzes(state: ReadingSessionState) -> ReadingSessionState:
    """세션 시작 직후 각 chunk로 O/X 퀴즈를 프리젠해 state["quizzes"]에 캐시한다(편지 §5-2).

    2번이 아직 chunk.summary를 산출하지 않으므로 요약 입력은
    summary → restructured_text → original_text 순으로 폴백한다.
    문단이 너무 짧거나 텍스트가 없으면 그 문단은 스킵한다(편지 §9 엣지케이스).
    """
    chunks = state.get("chunks") or []
    session_id = state.get("session_id", "")
    quizzes: dict = state.setdefault("quizzes", {})

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        chunk_id = chunk.get("chunk_id")
        if not chunk_id:
            continue
        chunk_id = str(chunk_id)

        paragraph = str(chunk.get("original_text") or chunk.get("restructured_text") or "")
        summary = str(
            chunk.get("summary")
            or chunk.get("restructured_text")
            or chunk.get("original_text")
            or ""
        )
        # 진술문으로 참·거짓을 물을 수 없을 만큼 짧은 문단은 스킵.
        if len(summary.strip()) < 8:
            continue

        quizzes[chunk_id] = generate_ox_quiz(summary, paragraph, chunk_id, session_id)

    return state


def pick_quiz(state: ReadingSessionState) -> dict | None:
    """트리거(A/B) + 쿨다운 + 상·하한 + 재출제 방지 후 낼 퀴즈를 고른다(편지 §5-3).

    반환값(quiz_data 사본, trigger 메타 포함)이 있으면 호출부(1번 /events 배선)가
    state["intervention"]["quiz_data"]에 주입한다. 없으면 None.
    """
    if not state.get("quizzes"):
        return None

    asked = state.setdefault("asked_quiz_ids", [])
    events = state.get("reading_events") or []
    now_ms = _latest_timestamp_ms(events)
    last_ms = state.get("last_quiz_at_ms")

    # 0) 상한 / 쿨다운
    if len(asked) >= MAX_QUIZZES:
        return None
    if last_ms is not None and (now_ms - last_ms) < COOLDOWN_MS:
        return None

    focus = _num(state.get("focus_score"), default=100.0)
    position = _max_position(events)

    # 1) 트리거 판정
    if focus < HARD_FOCUS_CUTOFF:
        trigger = "focus_drop"          # 재집중 + 측정
    elif position >= PROGRESS_FLOOR and len(asked) < MIN_QUIZZES:
        trigger = "progress_floor"      # 집중 잘한 사람 측정 보장
    else:
        return None

    # 2) 어느 문단 퀴즈? — 방금 읽던 position 기준(3번 select_quiz_for_state, 재출제 방지 포함)
    quiz = select_quiz_for_state(state)
    if quiz is None:
        return None

    # 3) 기록 후 반환
    quiz = dict(quiz)
    quiz["trigger"] = trigger
    asked.append(quiz["quizId"])
    state["last_quiz_at_ms"] = now_ms
    # 채점 시 trigger 메타를 quiz_answers에 남기기 위해 quizId→trigger를 보관.
    state.setdefault("quiz_triggers", {})[quiz["quizId"]] = trigger
    return quiz


QUIZ_INTERVENTION_MESSAGE = "방금 읽은 내용을 O/X 퀴즈로 확인해볼까요?"


def apply_pick_quiz(state: ReadingSessionState) -> ReadingSessionState:
    """pick_quiz 결과를 intervention 명령에 주입한다(1번 /events 배선용).

    routing.decide_intervention이 focus 기반 명령을 채운 **직후** 호출한다.
    퀴즈가 선택되면(집중 하락 또는 측정 보장) type을 "quiz"로 승격하고
    quiz_data를 실어 to_intervention_command가 payload.quiz로 노출하게 한다.
    집중이 좋아 개입이 "none"이던 경우에도 측정 보장 트리거는 퀴즈를 띄운다.
    """
    quiz = pick_quiz(state)
    if not quiz:
        return state

    intervention = dict(state.get("intervention") or {})
    intervention["type"] = "quiz"
    if intervention.get("level", "none") == "none":
        intervention["level"] = "hard"
    if not intervention.get("message"):
        intervention["message"] = QUIZ_INTERVENTION_MESSAGE
    intervention["quiz_data"] = quiz

    state["intervention"] = intervention
    state["intervention_needed"] = True
    state["intervention_level"] = intervention["level"]
    state["intervention_message"] = intervention["message"]
    return state


def submit_ox_quiz(state: ReadingSessionState, quiz_id: str, selected_option: str) -> dict | None:
    """O/X 답안을 채점하고 quiz_answers에 기록한다(편지 §5-4). 정답 시 집중 회복 + XP.

    반환(프론트 계약): {correct, explanation, focusRecovered, xpEarned}.
    quiz_id를 찾지 못하면 None(호출부가 404 처리).
    """
    quiz = _find_quiz(state, quiz_id)
    if quiz is None:
        return None

    selected_is_o = str(selected_option).strip().upper() == "O"
    correct = bool(selected_is_o == bool(quiz.get("answer")))
    trigger = state.get("quiz_triggers", {}).get(quiz_id)

    state.setdefault("quiz_answers", []).append(
        {
            "quizId": quiz_id,
            "sourceChunkId": quiz.get("sourceChunkId"),
            "correct": correct,
            "trigger": trigger,
        }
    )

    focus_recovered = 0.0
    xp_earned = 0
    if correct:
        focus = _num(state.get("focus_score"), default=0.0)
        state["focus_score"] = max(0.0, min(100.0, focus + FOCUS_RECOVERY))
        focus_recovered = FOCUS_RECOVERY
        xp_earned = XP_PER_QUIZ

    return {
        "correct": correct,
        "explanation": quiz.get("explanation", ""),
        "focusRecovered": focus_recovered,
        "xpEarned": xp_earned,
    }


def _find_quiz(state: ReadingSessionState, quiz_id: str) -> dict | None:
    for quiz in (state.get("quizzes") or {}).values():
        if isinstance(quiz, dict) and quiz.get("quizId") == quiz_id:
            return quiz
    return None


def _latest_timestamp_ms(events: list) -> int:
    stamps = [
        int(e["timestamp_ms"])
        for e in events
        if isinstance(e, dict) and isinstance(e.get("timestamp_ms"), (int, float))
    ]
    return max(stamps) if stamps else 0


def _max_position(events: list) -> float:
    positions = [
        _num(e.get("position"), default=0.0)
        for e in events
        if isinstance(e, dict) and e.get("position") is not None
    ]
    return max(positions) if positions else 0.0


def _num(value: object, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default
