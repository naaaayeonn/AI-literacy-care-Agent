"""Orchestrator E2E 흐름 테스트. [구현 예정: 6/22]

검증 항목(예정):
- raw_text 입력 → 최종 JSON에 literacy_score 포함
- 각 단계가 trace에 기록됨
- 한 stub 실패 시 fallback으로 흐름 유지
"""

import pytest


@pytest.mark.skip(reason="6/22 M0 stub 흐름 구현 후 작성")
def test_run_reading_session_placeholder():
    ...
