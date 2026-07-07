# 3. Cognitive Care Backend 딜리버리 플랜

## 1. 개요
이 문서는 3번 역할(Cognitive Care Backend)의 구현 계획 및 완료 현황을 추적하기 위한 플랜입니다. 현재 코어 시스템 구축과 주요 팀원(1번, 4번)과의 연동이 모두 완료된 상태입니다.

---

## 2. 마일스톤 및 완료 현황

### Phase 1 (M0): 인프라 및 프로젝트 스캐폴딩 (✅ 완료)
- [x] FastAPI 백엔드 프로젝트 기본 골격 구성
- [x] PostgreSQL 데이터베이스 스키마 및 SQLAlchemy ORM 모델 세팅 (`models.py`)
- [x] Redis 연결 설정 및 비동기 클라이언트 구성 (`redis.py`)

### Phase 2 (M1): Cognitive Care 핵심 엔진 구현 (✅ 완료)
- [x] 실시간 이벤트 기반 집중도 점수(`focus_score`) 계산 로직 구현
- [x] 점수에 따른 개입(Intervention) 단계 판별 로직 추가 (`determine_intervention`)
- [x] 관련 로직에 대한 단위 테스트(`pytest`) 작성 및 통과 확인

### Phase 3 (M2): 핵심 모듈 통합 (Core Integration) (✅ 완료)
- [x] **1번 오케스트레이터 연동**: `frontend_contract.py` 및 `state.py` 이식 완료
- [x] **4번 프론트엔드 웹소켓 동기화**: 단건 이벤트 수신 및 중첩 JSON 응답 구조 완벽 대응
- [x] **4번 프론트엔드 REST API 동기화**: `/start` 및 `/result` 스키마 갱신 및 어댑터 부착
- [x] 통합 테스트 및 `main` 브랜치 배포 완료

### Phase 4 (M3): 남은 외부 모듈 연동 (⏳ 진행 예정)
- [ ] **2번 Content & RAG 연동**: `/start` API의 목업 아티클을 실제 2번 요약 API 응답으로 교체
- [ ] **5번 QA & Evaluation 연동**: `/result` 최종 점수 산출 시 목업 퀴즈 점수(85점)를 실제 5번 퀴즈 모듈 결과로 교체

---

## 3. 최종 제출 체크리스트 (3번 역할 기준)
- [x] 실시간 이벤트 스트리밍 처리 (WebSocket)
- [x] 인메모리 버퍼링 및 RDBMS 영구 저장 파이프라인
- [x] 오케스트레이터 규격에 맞춘 어댑터 패턴 적용
- [x] 집중도 하락 시 프론트엔드에 개입(Nudge) 명령 전송
- [ ] 2번/5번 모듈 최종 통합
