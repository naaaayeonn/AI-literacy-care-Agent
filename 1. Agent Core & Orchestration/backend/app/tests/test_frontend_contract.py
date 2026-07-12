"""프론트 계약 변환 어댑터 검증.

M1 데모를 끝까지 돌린 뒤, 프론트(apps/web/src/lib/api.ts)가 기대하는
InterventionCommand / SessionResultResponse 형태로 변환되는지 확인한다.
"""

from __future__ import annotations

from backend.app.api.frontend_contract import (
    to_intervention_command,
    to_session_result,
)
from backend.app.demo.m1_scenario import build_m1_demo_state, run_m1_demo


def test_intervention_command_exposes_quiz_without_answer():
    # 개입이 quiz + quiz_data를 가지면 payload.quiz로 노출하되 정답(answer)은 제외한다.
    state = build_m1_demo_state()
    state["focus_score"] = 20.0
    state["intervention"] = {
        "type": "quiz",
        "level": "hard",
        "message": "잠깐! O/X로 확인해볼까요?",
        "quiz_data": {
            "quizId": "quiz_s1_c1",
            "type": "ox",
            "question": "이 문단은 X-선 파장이 가시광선보다 길다고 설명한다.",
            "statement": "이 문단은 X-선 파장이 가시광선보다 길다고 설명한다.",
            "options": ["O", "X"],
            "answer": False,
            "explanation": "본문은 '짧다'고 설명합니다.",
            "sourceChunkId": "c1",
        },
    }

    cmd = to_intervention_command(state)

    assert cmd["type"] == "quiz"
    quiz = cmd["payload"]["quiz"]
    assert quiz["quizId"] == "quiz_s1_c1"
    assert quiz["question"]  # 프론트 QuizData: 렌더할 진술문
    assert quiz["options"] == ["O", "X"]  # QuizCard O/X 2버튼 모드
    assert "answer" not in quiz  # 정답은 프론트로 나가면 안 됨(서버 채점)
    assert "explanation" not in quiz  # 해설도 정답을 노출하므로 채점 응답에서만 준다


def test_intervention_command_shape():
    state = run_m1_demo()  # stub 기준: focus 39 → medium/nudge
    cmd = to_intervention_command(state)

    # 프론트 InterventionCommand: { type, payload }
    assert cmd["type"] in {"nudge", "quiz", "highlight", "score_update", "session_end"}
    assert isinstance(cmd["payload"], dict)
    assert "focusScore" in cmd["payload"]
    assert "progress" in cmd["payload"]

    # 데모는 medium 개입 → nudge 타입 + nudgeLevel/Message 포함
    assert cmd["type"] == "nudge"
    assert cmd["payload"]["nudgeLevel"] == "medium"
    assert cmd["payload"]["nudgeMessage"]


def test_intervention_command_none_is_score_update():
    state = build_m1_demo_state()
    state["intervention"] = {"level": "none", "type": "none", "message": ""}
    state["focus_score"] = 90.0
    cmd = to_intervention_command(state)
    assert cmd["type"] == "score_update"
    assert "nudgeLevel" not in cmd["payload"]


def test_session_result_shape_and_keys():
    state = run_m1_demo()
    result = to_session_result(state)

    # 프론트 SessionResultResponse 필수 키 전부 존재
    expected_keys = {
        "sessionId",
        "literacyScore",
        "comprehensionScore",
        "engagementScore",
        "difficultyBonus",
        "completionRate",
        "xpEarned",
        "totalXp",
        "level",
        "scoreSeries",
        "badges",
        "sessionDurationMs",
    }
    assert expected_keys <= set(result.keys())

    # 점수 범위/타입 sanity
    assert 0.0 <= result["literacyScore"] <= 100.0
    assert isinstance(result["scoreSeries"], list) and len(result["scoreSeries"]) == 2
    assert isinstance(result["badges"], list)
    assert result["level"] >= 1


def test_session_result_score_series_uses_previous_profile():
    """scoreSeries가 이전 점수(64.0) 대비 현재 점수 개선 스토리를 만든다."""
    state = run_m1_demo()  # DEMO_PROFILE previous_literacy_score=64.0
    result = to_session_result(state)
    care_before = result["scoreSeries"][0]["after"]
    care_after = result["scoreSeries"][1]["after"]
    assert care_before == 64.0
    assert care_after == result["literacyScore"]


def test_badges_mapped_to_objects():
    state = run_m1_demo()  # reward.badge="needs_support"
    result = to_session_result(state)
    assert result["badges"]
    badge = result["badges"][0]
    assert {"id", "name", "emoji", "description", "acquiredAt"} <= set(badge.keys())


def test_completion_rate_from_events():
    state = run_m1_demo()  # 최대 position 0.68 → 68%
    result = to_session_result(state)
    assert result["completionRate"] == 68
