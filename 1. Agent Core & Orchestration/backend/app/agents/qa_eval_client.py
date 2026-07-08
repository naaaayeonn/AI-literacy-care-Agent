"""Adapter for the QA/Evaluation agent (5번)."""

from __future__ import annotations

from backend.app.orchestrator.state import ReadingSessionState


def run_qa_eval_agent(state: ReadingSessionState) -> ReadingSessionState:
    """5번 QA 모듈로 세션 상태를 평가하고 리포트를 state에 담는다.

    5번 진입점(PR #7 "feat(qa): add state-based evaluation entrypoint"):
        backend.evaluation.evaluation_pipeline.run_evaluation_from_state(state)

    - 리포트(faithfulness/relevance/average_score/passed/session_id/document_id/
      has_trace/has_errors)를 state["qa_evaluation"]에 저장한다.
    - QA는 품질 가드이므로 실패해도 폐루프를 끊지 않는다(예외 무전파, errors에만 기록).
    - import는 지연 로딩으로 두어 5번 모듈이 없거나 깨져도 세션이 죽지 않게 한다.
    """
    try:
        from backend.evaluation.evaluation_pipeline import run_evaluation_from_state

        state["qa_evaluation"] = run_evaluation_from_state(state)
    except Exception as exc:  # 데모 보호: QA 실패가 세션을 끊지 않게
        state.setdefault("errors", []).append({"step": "qa_eval", "error": str(exc)})
    return state
