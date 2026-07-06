"""통합 테스트 - M2 완성 검증 (7/6 구현)

Orchestrator 파이프라인 전체 흐름을 테스트합니다:
1. Score Engine 계산 정확성
2. Intervention 라우팅 정확성  
3. 전체 파이프라인 흐름 (생성 -> cognitive care -> routing -> score -> reward)
4. Fallback 동작
5. Reward 계산

실행: python -m pytest backend/app/tests/test_integration.py -v
"""

import pytest
import sys
import os

# backend 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestScoreEngine:
    """Score Engine 단위 테스트 (6/26 검증)."""
    
    def test_compute_score_basic(self):
        from app.orchestrator.score import compute_score
        score, breakdown = compute_score(
            quiz_correct_rate=0.8,
            focus_score=70.0,
            difficulty_score=60.0,
            abnormal_reading_penalty=0.0,
        )
        # 80*0.5 + 70*0.35 + 60*0.15 = 40 + 24.5 + 9 = 73.5
        assert 73.0 <= score <= 74.0, f"Expected ~73.5, got {score}"
        assert breakdown["comprehension_score"] == 80.0
        assert breakdown["engagement_score"] == 70.0
    
    def test_compute_score_with_penalty(self):
        from app.orchestrator.score import compute_score
        score, _ = compute_score(
            quiz_correct_rate=1.0,
            focus_score=100.0,
            difficulty_score=100.0,
            abnormal_reading_penalty=10.0,
        )
        # 100*0.5 + 100*0.35 + 100*0.15 - 10 = 50 + 35 + 15 - 10 = 90
        assert score == 90.0, f"Expected 90.0, got {score}"
    
    def test_compute_score_clamped(self):
        from app.orchestrator.score import compute_score
        score, _ = compute_score(
            quiz_correct_rate=0.0,
            focus_score=0.0,
            difficulty_score=0.0,
            abnormal_reading_penalty=50.0,
        )
        assert score == 0.0, "Score should be clamped to 0"
    
    def test_compute_score_nan_handling(self):
        from app.orchestrator.score import compute_score
        score, _ = compute_score(
            quiz_correct_rate=float('nan'),
            focus_score=70.0,
            difficulty_score=50.0,
        )
        # NaN -> 50 (midpoint), so 50*0.5 + 70*0.35 + 50*0.15 = 25 + 24.5 + 7.5 = 57
        assert 56.0 <= score <= 58.0, f"Expected ~57, got {score}"


class TestRouting:
    """Intervention 라우팅 테스트 (6/24 검증)."""
    
    def test_none_intervention(self):
        from app.orchestrator.routing import level_for_focus
        assert level_for_focus(90.0) == "none"
        assert level_for_focus(75.0) == "none"
    
    def test_soft_intervention(self):
        from app.orchestrator.routing import level_for_focus
        assert level_for_focus(74.9) == "soft"
        assert level_for_focus(50.0) == "soft"
    
    def test_medium_intervention(self):
        from app.orchestrator.routing import level_for_focus
        assert level_for_focus(49.9) == "medium"
        assert level_for_focus(30.0) == "medium"
    
    def test_hard_intervention(self):
        from app.orchestrator.routing import level_for_focus
        assert level_for_focus(29.9) == "hard"
        assert level_for_focus(0.0) == "hard"


class TestReward:
    """Reward 서비스 테스트 (7/1 검증)."""
    
    def test_xp_calculation(self):
        from app.services.reward_service import calculate_xp
        xp = calculate_xp(literacy_score=80.0, completed=True, streak_days=0)
        # 80 * 1.5 + 20 = 140
        assert xp == 140
    
    def test_xp_with_streak(self):
        from app.services.reward_service import calculate_xp
        xp = calculate_xp(literacy_score=80.0, completed=True, streak_days=3)
        # 80 * 1.5 + 20 + 15 = 155
        assert xp == 155
    
    def test_level_calculation(self):
        from app.services.reward_service import get_level_for_xp
        assert get_level_for_xp(0) == 1
        assert get_level_for_xp(99) == 1
        assert get_level_for_xp(100) == 2
        assert get_level_for_xp(300) == 3
        assert get_level_for_xp(1000) == 5
    
    def test_badge_first_read(self):
        from app.services.reward_service import check_badges
        badges = check_badges(total_sessions=1)
        badge_ids = [b["id"] for b in badges]
        assert "first-read" in badge_ids


class TestFullPipeline:
    """Orchestrator 전체 파이프라인 테스트 (7/5~7/6 검증)."""
    
    def test_full_reading_session(self):
        from app.orchestrator.state import create_initial_state
        from app.orchestrator.graph import run_reading_session
        
        state = create_initial_state(
            session_id="test-session-001",
            user_id="test-user",
            document_id="doc-001",
            raw_text="This is a test document.\n\nIt has multiple paragraphs.\n\nFor testing purposes.",
        )
        
        # 가상 읽기 이벤트 추가
        state["reading_events"] = [
            {"type": "scroll", "timestamp_ms": 1000, "metadata": {"position": 0.1}},
            {"type": "scroll", "timestamp_ms": 2000, "metadata": {"position": 0.3}},
            {"type": "focus", "timestamp_ms": 3000, "metadata": {}},
            {"type": "scroll", "timestamp_ms": 5000, "metadata": {"position": 0.7}},
            {"type": "scroll", "timestamp_ms": 7000, "metadata": {"position": 1.0}},
        ]
        
        # 퀴즈 결과 추가
        state["quiz_result"] = {
            "quiz_id": "quiz-001",
            "correct_count": 4,
            "total_count": 5,
            "answers": [],
        }
        
        # 파이프라인 실행
        result = run_reading_session(state)
        
        # 검증
        assert "literacy_score" in result
        assert "comprehension_score" in result
        assert "engagement_score" in result
        assert "focus_score" in result
        assert "reward" in result
        assert "trace" in result
        
        assert 0 <= result["literacy_score"] <= 100
        assert 0 <= result["comprehension_score"] <= 100
        assert 0 <= result["engagement_score"] <= 100
        assert result["reward"]["xp"] > 0
        
        # trace 검증
        trace_steps = [t["step"] for t in result["trace"]]
        assert "content_reducer" in trace_steps
        assert "cognitive_care" in trace_steps
        assert "score_engine" in trace_steps
        assert "reward" in trace_steps
    
    def test_pipeline_with_no_events(self):
        """이벤트 없이도 파이프라인이 정상 동작하는지 테스트."""
        from app.orchestrator.state import create_initial_state
        from app.orchestrator.graph import run_reading_session
        
        state = create_initial_state(
            session_id="test-empty",
            user_id="test-user",
            document_id="doc-002",
            raw_text="Empty test.",
        )
        
        result = run_reading_session(state)
        
        assert "literacy_score" in result
        assert result["literacy_score"] >= 0
        assert len(result["trace"]) > 0
    
    def test_pipeline_fallbacks(self):
        """각 단계의 fallback이 정상 동작하는지 테스트."""
        from app.orchestrator.state import create_initial_state, ReadingSessionState
        from app.orchestrator.errors import (
            apply_content_reducer_fallback,
            apply_cognitive_care_fallback,
            apply_score_fallback,
            apply_reward_fallback,
            apply_profile_fallback,
        )
        
        state = create_initial_state(
            session_id="test-fallback",
            user_id="test-user",
            document_id="doc-003",
            raw_text="Fallback test.",
        )
        
        # 각 fallback 적용
        state = apply_content_reducer_fallback(state, Exception("test error"))
        assert state["difficulty_score"] == 50.0
        
        state = apply_cognitive_care_fallback(state, Exception("test error"))
        assert state["focus_score"] == 60.0
        
        state = apply_score_fallback(state, Exception("test error"))
        assert "literacy_score" in state
        
        state = apply_reward_fallback(state, Exception("test error"))
        assert state["reward"]["xp"] == 0
        
        state = apply_profile_fallback(state, Exception("test error"))
        assert state["updated_profile"] == {}
        
        # 모든 fallback이 trace에 기록되었는지 확인
        fallback_traces = [t for t in state["trace"] if t["status"] == "fallback"]
        assert len(fallback_traces) == 5


class TestContracts:
    """Contract 검증 테스트 (M2 검증)."""
    
    def test_valid_contract(self):
        from app.orchestrator.contracts import validate_contract
        payload = {
            "focus_score": 80.0,
            "engagement_score": 75.0,
            "intervention_needed": False,
            "intervention_level": "none",
        }
        # 예외 없이 통과해야 함
        validate_contract("cognitive_care", payload)
    
    def test_invalid_contract(self):
        from app.orchestrator.contracts import validate_contract, ContractValidationError
        payload = {"focus_score": 80.0}  # 필수 필드 누락
        with pytest.raises(ContractValidationError):
            validate_contract("cognitive_care", payload)
    
    def test_unknown_contract_passes(self):
        from app.orchestrator.contracts import validate_contract
        validate_contract("unknown_agent", {})  # 예외 없이 통과


class TestCognitiveCare:
    """기존 Cognitive Care 테스트 확장."""
    
    def test_focus_score_no_events(self):
        from app.services.cognitive_care import calculate_focus_score
        assert calculate_focus_score([]) == 100.0
    
    def test_focus_score_with_blur(self):
        from app.services.cognitive_care import calculate_focus_score
        events = [
            {"type": "blur", "duration_ms": 5000},
            {"type": "scroll"},
            {"type": "focus"},
        ]
        score = calculate_focus_score(events)
        assert score < 100.0, "Blur events should reduce focus score"
    
    def test_intervention_levels(self):
        from app.services.cognitive_care import determine_intervention
        
        needed, level, msg = determine_intervention(90.0)
        assert not needed
        
        needed, level, msg = determine_intervention(50.0)
        assert needed
        assert level == "medium"


class TestRAGService:
    """Strict RAG 및 Fallback 서비스 검증 테스트 (7/7~7/9 M3)."""
    
    @pytest.mark.anyio
    async def test_explain_term_with_context(self):
        from app.services.rag_service import explain_term_with_rag
        
        raw_text = (
            "디지털 문명에서 글을 정확하게 해석하는 리터러시 역량은 매우 중요합니다. "
            "이 능력을 통해 가짜 정보를 판별하고 비판적 사고를 기를 수 있습니다."
        )
        
        # 지문 내 단어 RAG 조회 -> 지문 맥락이 담긴 답변 리턴 검증
        explanation = await explain_term_with_rag(term="리터러시", raw_text=raw_text)
        
        assert "리터러시" in explanation
        assert "📌 지문 속 맥락" in explanation
        assert "글을 정확하게 해석하는 리터러시 역량은 매우 중요합니다." in explanation
        
    @pytest.mark.anyio
    async def test_explain_term_fallback_dictionary(self):
        from app.services.rag_service import explain_term_with_rag
        
        # 지문에 존재하지 않는 핵심 단어 -> 사전 정의 제공
        explanation = await explain_term_with_rag(term="LLM", raw_text="임의의 지문 텍스트입니다.")
        
        assert "LLM" in explanation
        assert "[AI 설명]" in explanation
        assert "대규모 텍스트 데이터" in explanation
        
    @pytest.mark.anyio
    async def test_explain_term_unknown_term(self):
        from app.services.rag_service import explain_term_with_rag
        
        # 사전에 없는 단어 -> 일반 범용 설명 리턴
        explanation = await explain_term_with_rag(term="미정의단어", raw_text="임의의 텍스트")
        
        assert "미정의단어" in explanation
        assert "일반 정의입니다" in explanation

