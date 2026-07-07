"""오케스트레이터 코어 패키지 (1번 역할 핵심 산출물).

이 패키지가 프로젝트의 중앙 엔진이다. 모든 에이전트는 여기 정의된
Shared State(`state.py`)를 읽고 쓰며, 실행 순서는 `graph.py`가 결정한다.

구성:
- state.py     : Shared State 스키마 (ReadingSessionState 등)  [핵심]
- graph.py     : 에이전트 실행 흐름 (orchestrator flow)
- routing.py   : 집중도 기반 개입(intervention) 라우팅
- score.py     : Literacy Score 계산 (순수 함수)              [핵심]
- contracts.py : 팀원별 입출력 계약 (런타임 검증용)
- errors.py    : 에이전트 실패 시 fallback 정의
"""
