# Delivery Plan

## 1. 문서 목적

이 문서는 2026 AI/SW 경진대회 프로젝트에서 **2번 역할: 콘텐츠 처리 / RAG 기술리드**를 완수하기 위한 개발 실행 계획을 정리한다.

`ARCHITECTURE_2.md`가 "무엇을 어떤 구조로 만들 것인가"를 설명하는 문서라면, 이 문서는 "언제, 어떤 순서로, 어디까지 구현할 것인가"를 정의한다.

2번 역할의 핵심은 앱 전체 구현이 아니라, Orchestrator(1번)가 요청하는 원문을 수준에 맞게 재구성하고, 신뢰 출처 기반의 용어풀이와 문맥 맞춤형 퀴즈를 제공하여 **폐루프 시스템의 콘텐츠 처리 엔진**을 완성하는 것이다.

---

## 2. 전체 개발 목표

최종 목표는 팀 전체 산출물인 AI 리터러시 케어 데모 안에서 2번 역할이 담당하는 콘텐츠 처리 시스템을 안정적으로 동작시키는 것이다.

2번 역할의 최종 산출물:

- 가독성 분석 모듈 및 difficulty_score 산출
- 의미 단위 청킹(Semantic Chunking) 및 chunk_id 규칙
- LLM 기반 쉬운 문장 재구성 (난이도별 모델 라우팅)
- RAG 기반 신뢰 출처 용어풀이 엔진
- 문맥 맞춤형 인터랙티브 퀴즈 생성기
- Stub 기반 E2E 연결 (1번 Orchestrator 호환)
- 입출력 타입 정의 및 팀원 계약 문서
- Fallback 처리 구조
- 핵심 단위 테스트 및 E2E 통합 테스트

최종 데모에서 2번 역할이 보장해야 하는 흐름:

```text
원문 입력
→ 가독성 지수 분석 및 difficulty_score 산출
→ 의미 단위 청킹 (chunk_id 부여)
→ 사용자 수준에 맞게 쉬운 문장으로 재구성
→ RAG 기반 전문 용어 추출 및 툴팁 풀이 생성
→ Orchestrator에 chunks / terms / difficulty_score 반환
→ (집중도 저하 트리거 수신 시) 해당 chunk 문맥 기반 퀴즈 생성
→ quiz 객체를 Orchestrator에 반환
```

---

## 3. Scope Definition

### 2번 역할이 책임지는 것

| 영역 | 책임 내용 |
|---|---|
| Readability Analysis | 한국어 가독성 지수 계산 및 difficulty_score 산출 |
| Semantic Chunking | 의미 단위 문단 분할 및 chunk_id 규칙 정의 |
| LLM Restructuring | 사용자 프로필 기반 쉬운 문장 변환 및 LLM 라우팅 |
| RAG Grounding | 신뢰 출처 Vector DB 기반 용어풀이 생성 |
| Faithfulness Validation | Ragas 기반 용어풀이 품질 검증 |
| Quiz Generation | chunk 문맥 기반 사지선다형 퀴즈 동적 생성 |
| Stub E2E | 실제 LLM 없이 1번 E2E 흐름을 지원하는 stub 구현 |
| Integration | 1번 Orchestrator와 호환되는 agent.py 인터페이스 |
| Fallback | 각 서브모듈 실패 시 기본값 처리 |
| Contract Doc | 팀원별 입출력 JSON 계약 문서화 |
| Core Tests | readability / chunker / rag / quiz 단위 테스트 |

### 2번 역할이 직접 책임지지 않는 것

| 영역 | 주 담당 | 2번의 관여 |
|---|---|---|
| Orchestrator 실행 흐름 | 1번 오케스트레이션 | 입출력 계약 준수, state 병합 형식 협의 |
| WebSocket 행동 데이터 수집 | 3번 백엔드 | chunk_id 규칙 공유 |
| PostgreSQL/Redis 인프라 | 3번 백엔드 | pgvector 접속 정보 협의 |
| 읽기 화면 UI 구현 | 4번 프론트 | chunks / terms JSON 형식 제공 |
| 툴팁 UI 컴포넌트 구현 | 4번 프론트 | term 구조 정의 |
| Ragas 평가 파이프라인 구성 | 5번 QA | faithfulness_score / trace 데이터 제공 |
| Literacy Score 계산 | 1번 오케스트레이션 | difficulty_score 형식(0~100) 준수 |
| 배포 인프라 설정 | 3번 백엔드 | 환경 변수 공유 |

---

## 4. Milestone Overview

| Milestone | Date | Goal | Done When |
|---|---:|---|---|
| M0 | 6/22 | Stub E2E 및 계약 초안 | 1번 Orchestrator가 stub으로 전체 흐름 실행 가능 |
| M1 | 6/29 | 핵심 콘텐츠 파이프라인 완성 | 원문 → 청킹 → 재구성 → 용어풀이 흐름 동작 |
| M2 | 7/6 | 퀴즈 생성 및 전 기능 통합 | 퀴즈 생성 + 1번 실제 Orchestrator 연결 |
| **ME** | **7/6~7/9** | **확장(Chrome) 대응 — 2번 추가 작업** | **content[] 정규화 + PDF 문단 재구성 + 무료 용어풀이 완료** |
| M3 | 7/10 | 기능 동결 | **웹/PDF/용어풀이 포함 전 기능 완성**, 이후 구조 변경 없이 버그 수정만 |
| — | 7/11~7/14 | **버그 수정·검토만** | 신규 기능·구조 변경 금지, 데모 고정·리허설 |
| Final | 7/15 | 프로그램 제출 | 팀 최종 산출물 제출 |

> **일정 원칙(확장 반영)**: 확장 추가 작업(ME)은 M2 직후 7/6~7/9에 진행하고 **7/10(M3)에
> 웹·PDF·용어풀이까지 모든 모델/기능을 동결**한다. **7/11~7/14는 버그 수정·검토만** 하고,
> **7/15에 제출**한다. 확장 대응 상세 작업 분해는 §27-E를 참조한다.

---

## 5. Phase 0 Goal: 문서와 기준 확정

Phase 0에서는 구현보다 기준 확정을 우선한다. 2번 역할은 1번 Orchestrator가 stub을 사용해 E2E 흐름을 먼저 돌릴 수 있도록 계약과 stub을 먼저 제공해야 한다.

## Phase 0 완료 기준

- `ARCHITECTURE_2.md`가 존재한다.
- `DELIVERY_PLAN_2.md`가 존재한다.
- 2번 역할의 책임 범위가 명확하다.
- chunk_id 규칙이 팀 전체에 공유되었다.
- `ContentReducerRequest` / `ContentReducerResponse` 타입 초안이 있다.
- `content_reducer_stub.py`가 1번 E2E에서 동작한다.

---

## 6. Phase 0 Must Have

| Task | Description | Done When |
|---|---|---|
| Architecture document | 2번 역할 중심 아키텍처 문서 작성 | `ARCHITECTURE_2.md` 존재 |
| Delivery plan | 구현 순서와 완료 기준 작성 | `DELIVERY_PLAN_2.md` 존재 |
| Role boundary | 2번이 할 일/안 할 일 구분 | 문서에 Scope Definition 포함 |
| chunk_id rule | 팀 전체 공통 청크 식별자 규칙 정의 | chunk 규칙이 팀에 공유됨 |
| Contract draft | 입출력 JSON 계약 초안 | TypedDict 정의와 JSON 예시가 문서에 있음 |
| Stub implementation | 더미 Content Reducer | `content_reducer_stub.py` 존재 |

---

## 7. Phase 0 Should Have

| Task | Description | Done When |
|---|---|---|
| Docs folder plan | 추가 문서 위치 정의 | `docs/` 구조가 계획에 있음 |
| Test plan draft | 테스트 대상 정의 | readability/chunker/rag/quiz 테스트 항목 존재 |
| LLM routing rule | 난이도 기반 모델 선택 기준 문서화 | 기준이 문서에 기술됨 |

---

## 8. Phase 0 Not Today

Phase 0에서는 아래를 구현하지 않는다:

- 실제 LLM API 호출
- 실제 Vector DB 연동
- 실제 Ragas 평가 실행
- 실제 퀴즈 생성 LLM 호출
- 프론트엔드 연동

---

## 9. Phase 1 Goal: M0 콘텐츠 베이스 구현

Phase 1의 목표는 6/22까지 **실제 LLM 없이도 1번 Orchestrator의 전체 흐름이 한 번 도는 stub**을 제공하고, 가독성 분석과 청킹의 기반 구조를 갖추는 것이다.

## Phase 1 완료 기준

- Python 프로젝트 기본 구조가 있다.
- `content_reducer_stub.py`가 Orchestrator E2E에서 동작한다.
- `contracts.py`에 입출력 타입이 정의되어 있다.
- `readability.py` 함수가 동작한다.
- `chunker.py` 함수가 동작한다.
- 단위 테스트 최소 2개가 있다.

---

## 10. Phase 1 Must Have

| Task | Description | Done When |
|---|---|---|
| Project scaffold | 콘텐츠 에이전트 폴더 생성 | `backend/app/agents/content_reducer/` 존재 |
| contracts.py | 입출력 TypedDict 정의 | `ContentReducerRequest`, `ContentReducerResponse` 존재 |
| Stub agent | 더미 Content Reducer 작성 | 1번 Orchestrator stub 흐름에서 동작 |
| readability.py | 가독성 지수 계산 함수 | `analyze_readability(text) -> float` 반환 |
| chunker.py | 의미 단위 청킹 함수 | chunk_id 규칙 포함한 ChunkDict 반환 |
| fallbacks.py | 서브모듈 실패 시 기본값 | 각 모듈별 fallback 정의 |
| Basic tests | 핵심 함수 테스트 | `test_readability.py`, `test_chunker.py` 통과 |

---

## 11. Phase 1 Should Have

| Task | Description | Done When |
|---|---|---|
| API contract doc | 팀원별 JSON 계약 문서 | `docs/CONTENT_AGENT_CONTRACT.md` 존재 |
| Readability formula doc | 가독성 계산식 설명 | `docs/READABILITY_FORMULA.md` 존재 |
| Trace v0 | 단계별 실행 로그 | state의 trace에 step/status 누적 |
| agent.py skeleton | 에이전트 진입점 뼈대 | `run_content_reducer(state)` 함수 존재 |

---

## 12. Phase 1 Not Today

Phase 1에서는 아래 기능을 구현하지 않는다:

- 실제 LLM 재구성 (Claude API 호출)
- 실제 RAG 검색 (Vector DB 연동)
- Ragas 평가 실행
- 퀴즈 생성기 구현
- 3번/4번 팀원과의 실제 연결

---

## 13. Phase 2 Goal: M1 핵심 콘텐츠 파이프라인 완성

Phase 2의 목표는 6/29까지 **실제 LLM을 사용한 텍스트 재구성과 RAG 용어풀이가 동작하는 콘텐츠 파이프라인**을 완성하는 것이다.

핵심은 "ChatGPT 요약이 아니라, 사용자의 수준에 맞게 재구성하고 신뢰 출처 기반으로 풀이한다"는 것을 데모로 증명하는 것이다.

## Phase 2 완료 기준

- 원문 입력 → 청킹 → 재구성 → 용어풀이의 전체 흐름이 동작한다.
- difficulty_score가 계산되어 1번 Score Engine에 전달 가능하다.
- 각 chunk에 restructured_text가 포함되어 있다.
- terms 배열에 term, definition, source가 포함되어 있다.
- 프론트가 사용할 수 있는 chunks / terms JSON이 반환된다.
- 서브모듈 실패 시 fallback이 동작한다.

---

## 14. Phase 2 Must Have

| Task | Related Requirement | Done When |
|---|---|---|
| LLM routing | 난이도 기반 모델 선택 | difficulty_score 기준 Claude Sonnet / Haiku 분기 |
| restructurer.py | 쉬운 문장 변환 구현 | restructured_text가 각 chunk에 포함 |
| prompts.py | 재구성 프롬프트 템플릿 | 프롬프트가 파일로 분리되어 관리됨 |
| rag_engine.py | Vector DB 용어풀이 | term, definition, source 포함한 terms 반환 |
| pgvector 데이터 구축 | 신뢰 출처 임베딩 저장 | 최소 100개 이상 IT/일반 용어 저장 |
| Faithfulness 검증 | 환각 방지 | faithfulness_score가 term에 포함 |
| E2E demo data | 샘플 뉴스/논문 1편 | 반복 가능한 데모 입력 데이터 존재 |
| M1 smoke test | 핵심 흐름 검증 | 한 명령으로 파이프라인 실행 가능 |

---

## 15. Phase 2 Should Have

| Task | Description | Done When |
|---|---|---|
| Faithfulness threshold | 품질 기준 설정 | faithfulness_score < 0.8 시 경고 기록 |
| LLM failure fallback | LLM 실패 시 원문 반환 | restructured_text = original_text 처리 |
| RAG failure fallback | Vector DB 실패 시 빈 배열 | terms = [] 처리 |
| Frontend sample JSON | 프론트용 응답 샘플 | JSON 예시를 4번 팀원과 공유 |
| Manual demo script | 시연 순서 문서화 | 3분 안에 설명 가능한 시나리오 존재 |
| RAG architecture doc | RAG 파이프라인 문서 | `docs/RAG_ARCHITECTURE.md` 작성 |

---

## 16. Phase 2 Not Today

Phase 2에서는 아래를 후순위로 둔다:

- 퀴즈 생성기 구현 (Phase 3에서 완성)
- Ragas 자동 평가 파이프라인 (5번 QA 담당)
- 도메인별 용어집 완전 구축
- 세밀한 개인화 재구성 알고리즘
- 프론트엔드 UI 구현

---

## 17. Phase 3 Goal: M2 퀴즈 생성 및 전 기능 통합

Phase 3의 목표는 7/6까지 **퀴즈 생성기를 완성하고, 실제 1번 Orchestrator와 연결**하는 것이다.

이 시점부터 2번 역할은 구현자이면서 통합 담당자다. 1번이 stub 대신 실제 2번 모듈을 연결할 수 있도록 adapter 인터페이스를 안정화한다.

## Phase 3 완료 기준

- `quiz_generator.py`가 chunk_id와 context를 받아 퀴즈를 생성한다.
- 퀴즈 유효성 검사가 동작한다.
- 1번 Orchestrator에 실제 `run_content_reducer(state)`를 연결한다.
- stub과 실제 구현을 설정으로 교체할 수 있다.
- 3번이 chunk_id로 행동 데이터와 매핑 가능하다.
- 4번 프론트가 chunks/terms JSON을 렌더링할 수 있다.

---

## 18. Phase 3 Must Have

| Task | Related Module | Done When |
|---|---|---|
| quiz_generator.py | 퀴즈 생성 구현 | generate_quiz(chunk_id, context) 동작 |
| Quiz validation | 퀴즈 유효성 검사 | 4개 선택지, correct_option(1~4), explanation 검증 |
| Quiz fallback | 생성 실패 시 기본 퀴즈 | fallback_quiz 반환 |
| Orchestrator 연결 | 1번 통합 | 실제 run_content_reducer(state) 연결 완료 |
| Stub toggle | 통합 전환 | stub/real 모듈 설정 파일로 전환 가능 |
| Integration checklist | 팀 조율 | 팀원별 연결 상태 확인 가능 |
| test_quiz_generator.py | 퀴즈 생성 테스트 | 퀴즈 구조 및 유효성 테스트 통과 |

---

## 19. Phase 3 Should Have

| Task | Description | Done When |
|---|---|---|
| Quiz design doc | 퀴즈 생성 규칙 문서화 | `docs/QUIZ_DESIGN.md` 작성 |
| Contract validation | 입력/출력 검증 | 필수 필드 누락 시 명확한 error |
| Latency log | 실행 시간 측정 | trace에 latency_ms 기록 |
| Integration tests | 실제 모듈 포함 테스트 | `test_content_e2e.py` 통과 |
| Ragas 1차 평가 | 품질 측정 | faithfulness 평균 0.85 이상 달성 |

---

## 20. Phase 3 Not Today

Phase 3에서는 아래를 무리해서 넣지 않는다:

- 도메인별 완전한 용어집 구축
- Ragas 자동 평가 파이프라인 (5번 QA 담당)
- 스트리밍 방식 청크별 점진적 반환
- 관리자 대시보드 연동
- 고급 개인화 알고리즘

---

## 21. Phase 4 Goal: M3 기능 동결과 안정화

Phase 4의 목표는 7/10까지 구조 변경을 멈추고, **데모가 깨지지 않게 안정화**하는 것이다.

## Phase 4 완료 기준

- 기능 추가보다 버그 수정만 진행한다.
- 핵심 데모 시나리오가 반복 실행된다.
- 각 fallback이 정상 동작한다.
- difficulty_score 계산 근거가 발표에서 설명 가능하다.
- faithfulness_score가 0.8 이상인 용어풀이 비율이 90% 이상이다.

---

## 22. Phase 4 Must Have

| Task | Description | Done When |
|---|---|---|
| Freeze core contract | 입출력 스키마 변경 중단 | 팀원에게 최종 계약 공지 |
| Bug triage | 통합 오류 우선순위 정리 | 치명/중요/경미 구분 |
| Fallback hardening | 실패 시 데모 유지 | 각 서브모듈 실패해도 결과 반환 |
| difficulty_score sanity | 점수 비정상값 방지 | 0~100 clamp, NaN 방지 |
| Demo regression | 반복 실행 확인 | 같은 원문 기준 3회 이상 동일 결과 |

---

## 23. Phase 4 Should Have

| Task | Description | Done When |
|---|---|---|
| Cost/latency note | 발표용 LLM 비용 근거 | 고난도만 Sonnet, 나머지 Haiku 근거 설명 가능 |
| QA result hook | QA 결과 연결 | faithfulness_score를 trace 또는 admin data로 확인 |
| Final architecture update | 문서 최신화 | 실제 구현과 문서 차이 반영 |
| Demo fallback data | 비상용 샘플 결과 | API 실패 시 사용할 JSON 준비 |

---

## 24. Phase 4 Not Today

Phase 4에서는 아래 변경을 하지 않는다:

- 입출력 계약 구조 변경
- RAG 파이프라인 전면 교체
- 청킹 기준 전면 변경
- 프롬프트 템플릿 구조 재설계
- 새로운 용어집 도메인 추가
- 새로운 기능 추가

---

## 25. Phase 5 Goal: M4 제출본 점검

Phase 5의 목표는 7/14까지 제출 가능한 상태를 확인하고, **2번 역할의 콘텐츠 파이프라인을 발표에서 설명할 수 있게 준비**하는 것이다.

## Phase 5 완료 기준

- 최종 데모 플로우에서 2번 파이프라인이 안정적이다.
- 발표자가 RAG 환각 방지 구조를 설명할 수 있다.
- 심사 질문에 대한 기술 방어 근거가 있다.
- 제출본에서 콘텐츠 처리 기능이 누락되지 않는다.

---

## 26. Phase 5 Must Have

| Task | Description | Done When |
|---|---|---|
| Final demo rehearsal | 콘텐츠 파이프라인 리허설 | 원문→재구성→용어풀이→퀴즈 설명 가능 |
| Submission check | 제출본 점검 | 누락 파일/환경 변수 확인 |
| Defense script | 심사 질문 대비 | RAG 환각 방지, faithfulness 답변 준비 |
| Final smoke test | 최종 실행 확인 | 제출 전 파이프라인 전체 흐름 성공 |
| Docs sync | 문서와 구현 일치 | ARCHITECTURE_2.md / DELIVERY_PLAN_2.md 최신화 |

---

## 27. 2번 역할 Daily Task Plan

| Date | Goal | Must Finish |
|---|---|---|
| 6/20 | 프로젝트 골격 및 계약 초안 | 폴더 구조 생성, contracts.py TypedDict 초안, chunk_id 규칙 확정 |
| 6/21 | Stub 구현 및 팀 공유 | content_reducer_stub.py, 1번과 계약 협의, chunk_id 팀 공유 |
| 6/22 | M0 Stub E2E 연결 | 1번 Orchestrator가 stub으로 전체 흐름 실행 가능 |
| 6/23 | 가독성 분석 구현 | analyze_readability() 구현, test_readability.py 통과 |
| 6/24 | 의미 단위 청킹 구현 | semantic_chunk() 구현, chunk_id 포함 ChunkDict 반환 |
| 6/25 | LLM 재구성 프롬프트 설계 | prompts.py 작성, restructurer.py 뼈대 구현 |
| 6/26 | LLM 재구성 완성 | restructure_text() 동작, LLM 라우팅 분기 구현 |
| 6/27 | RAG 용어풀이 1차 구현 | pgvector 연동, 용어 임베딩 저장, 유사도 검색 동작 |
| 6/28 | RAG faithfulness 검증 | faithfulness_score 계산 포함, test_rag_engine.py 통과 |
| 6/29 | M1 완료 | 원문→청킹→재구성→용어풀이 전체 파이프라인 동작 |
| 6/30 | 퀴즈 생성기 구현 | generate_quiz() 구현, 유효성 검사 포함 |
| 7/1 | 퀴즈 완성 + Ragas 1차 | test_quiz_generator.py 통과, faithfulness 평균 측정 |
| 7/2 | 최소 작업 | 프롬프트 미세조정, 용어집 데이터 추가 수집 |
| 7/3 | 최소 작업 | 계약 변경사항 1번과 동기화, 문서 업데이트 |
| 7/4 | 최소 작업 | 테스트 케이스 보강, 엣지 케이스 처리 |
| 7/5 | 통합 보강 | 1번 Orchestrator와 실제 모듈 연결 준비 ✅ |
| 7/6 | M2 완료 + 확장 착수 | 1번 실제 연결 + test_content_e2e.py 통과 ✅ / 확장 인입(content[]) 정합 검토 시작 |
| 7/7 | 확장 ① content[] 정규화 | web=Readability / PDF=pdf.js **동일 content[]** 정규화, `_content_to_raw_text` 반복라인 제거 강화 + 테스트 |
| 7/8 | 확장 ② PDF 문단 재구성 | `itemsToParagraphs` 머리말/꼬리말(반복 라인) 제거 추가, 스캔 PDF 폴백 검증 |
| 7/9 | 확장 ③ 무료 용어풀이 | `POST /api/terms/lookup`(세션캐시→로컬사전→RAG 재사용, 유료 금지) + (선택) 문단 난이도 태그 |
| 7/10 | **M3 완료 — 전 기능 동결** | 웹/PDF/용어풀이 포함 모든 모델·기능 완성, 이후 구조 변경 금지 |
| 7/11 | 버그 수정·검토만 | 잔여 버그 수정 (기능 추가·구조 변경 없음) |
| 7/12 | 버그 수정·검토만 | 데모 데이터 고정, fallback 경로 재확인 |
| 7/13 | 버그 수정·검토만 | RAG 환각 방지·확장 시연 리허설 |
| 7/14 | 검토 마감 | 제출본 점검 (누락 파일/환경 변수/시연 흐름 반복) |
| 7/15 | 제출 | 프로그램 최종 제출 |

---

## 27-E. 확장(Chrome) 대응 — 2번 추가 작업 상세 (Phase E, 7/6~7/9)

> 근거: `docs/EXTENSION_DESIGN.md` §10(2번) / §13-6. 설계 상세는 `2_ARCHITECTURE.md` §12.
> 원칙: **코어(이벤트→개입→점수)·계약 불변.** 이번 추가는 "새 입력원(웹/PDF) 정규화 +
> 단어 무료 용어풀이"뿐이다. 웹↔PDF 중복을 만들지 않는다.

### 이미 완료된 부분 (확인)

- [x] 확장 인입 라우트 `POST /api/session/start`가 `content[]`를 받아 세션 시작 (`extension_session.py`)
- [x] `_content_to_raw_text`: `content[]` → `raw_text` 기본 정규화(strip·빈문자 제거·`\n\n` join)
- [x] 세션 시작 시 `run_content_reducer`로 기존 청킹/재구성/RAG 파이프라인 재사용 (계약 불변)
- [x] PDF 문단 재구성 1차: y좌표 줄분리·`hasEOL`·빈줄 문단분리·하이픈 병합 (`viewer.js itemsToParagraphs`)
- [x] 스캔 PDF(텍스트 레이어 없음) 안내 문단 폴백

### 남은 추가 작업 (7/6~7/9 완료 목표)

| # | Task | 담당 경계 | Done When |
|---|---|---|---|
| E1 | **content[] 정규화 동일화** | 2번 | web=Readability / PDF=pdf.js 결과가 **같은 문단 배열 형태**로 백엔드에 도달함이 테스트로 확인됨 |
| E2 | **반복 머리말/꼬리말 제거** | 2번 | `_content_to_raw_text`(또는 `itemsToParagraphs`)가 여러 페이지 반복 라인(제목·쪽번호)을 빈도·길이 이중 조건으로 제거 |
| E3 | **무료 용어풀이 lookup** | 2번 | `POST /api/terms/lookup`이 단어→`TermDict` 반환. 세션캐시→로컬사전→RAG 재사용 순, **유료 API 미사용**. 미발견 시 `source="not_found"` |
| E4 | (선택) **문단 난이도 태그** | 2번 | 어려운 문단 우선 개입용 `difficulty` 데이터를 3번에 제공(계약 변경 없음) |
| E5 | **확장 인입 테스트** | 2번 | `test_extension_session.py`에 web/PDF content[] 정규화·반복라인 제거·lookup 케이스 추가 후 통과 |

### Phase E 완료 기준 (7/9)

- 웹페이지·PDF 어느 쪽에서 들어와도 **동일 `content[]` 계약**으로 파이프라인이 동작한다.
- PDF 본문에서 반복 머리말/꼬리말·쪽번호가 청킹 노이즈로 새지 않는다.
- 단어 hover 용어풀이가 **비용 0 경로**로 뜻을 반환하고, 없으면 조용히 폴백한다.
- 기존 `contracts.py`·팀원 연결은 **깨지지 않는다**(신규 계약은 `terms/lookup` 하나뿐).

### Phase E Not Today (범위 밖)

- 스캔 PDF OCR(Tesseract.js) — 후속 트랙
- 크롬 밖 다른 뷰어/앱 창 측정 — 네이티브 에이전트 별도 트랙
- 유료 사전/번역 API 도입 — 비용 0 원칙 위반, 금지

---

## 28. Manual QA for M0

M0 종료 전 확인할 항목:

- [x] `backend/app/agents/content_reducer/` 폴더가 있다.
- [x] `2_ARCHITECTURE.md`가 있다. (현재 `2/2_ARCHITECTURE.md`로 이동 및 정리 완료)
- [x] `2_DELIVERY_PLAN.md`가 있다. (현재 `2/2_DELIVERY_PLAN.md`로 이동 및 정리 완료)
- [x] `contracts.py`에 `ContentReducerRequest`, `ContentReducerResponse` 타입이 있다.
- [x] `content_reducer_stub.py`가 있다.
- [x] stub이 1번 Orchestrator E2E 흐름에서 동작한다.
- [x] stub 출력에 `chunks`, `terms`, `difficulty_score` 필드가 있다.
- [x] stub 출력에 `trace` 기록이 있다.
- [x] chunk_id 규칙이 팀 전체에 공유되었다.
- [x] `readability.py`와 `chunker.py`의 최소 테스트가 있다.

---

## 29. Manual QA for M1

M1 종료 전 확인할 항목:

- [x] 샘플 뉴스/논문 1편으로 파이프라인이 실행된다.
- [x] `difficulty_score`가 0~100 범위로 반환된다.
- [x] 원문이 3개 이상의 chunk로 분할된다.
- [x] 각 chunk에 `chunk_id`, `char_start`, `char_end`가 포함된다.
- [x] 각 chunk에 `restructured_text`가 포함된다.
- [x] `terms` 배열에 `term`, `definition`, `source`가 있다.
- [x] `faithfulness_score`가 term에 포함된다.
- [x] LLM 실패 시 원문이 그대로 반환된다.
- [x] RAG 실패 시 `terms = []`이 반환된다.
- [x] 파이프라인이 3회 반복 실행되어도 실패하지 않는다.

---

## 30. Manual QA for M2

M2 종료 전 확인할 항목:

- [x] 1번 Orchestrator에 실제 `run_content_reducer(state)` 모듈이 연결된다.
- [x] 3번 행동 데이터의 `chunk_id`와 2번 청킹의 `chunk_id`가 일치한다.
- [x] 4번 프론트가 `chunks` / `terms` JSON을 렌더링할 수 있다.
- [x] 5번 QA가 `faithfulness_score`와 `trace`를 받을 수 있다.
- [x] `generate_quiz(chunk_id, context)`가 유효한 퀴즈를 반환한다.
- [x] 퀴즈 유효성 검사 실패 시 fallback 퀴즈가 반환된다.
- [x] stub/real 모듈 전환 방식이 있다.
- [x] `test_content_e2e.py`가 통과한다.

---

## 30-E. Manual QA for 확장 (Phase E)

Phase E(7/9) 종료 전 확인할 항목:

- [x] 웹페이지 `content[]`와 PDF `content[]`가 **동일 형태(문단 문자열 배열)**로 백엔드에 도달한다.
- [x] `POST /api/session/start`가 web·PDF 양쪽 `content[]`로 세션을 시작하고 chunks/terms를 반환한다.
- [x] PDF 본문에서 반복 머리말/꼬리말·쪽번호가 문단으로 새어들지 않는다.
- [x] 스캔(텍스트 레이어 없는) PDF에서 안내 문단 폴백이 동작한다.
- [x] `POST /api/terms/lookup`이 단어→`TermDict`(term/definition/source)를 반환한다.
- [x] 용어풀이가 **유료 API 없이** 세션캐시/로컬사전/기존 RAG 경로로만 동작한다.
- [x] 미발견 단어는 `source="not_found"`로 반환되어 프론트가 조용히 무시할 수 있다.
- [x] `test_extension_session.py`에 확장 인입·정규화·lookup 케이스가 추가되어 통과한다.
- [x] 확장 추가로 기존 `test_content_e2e.py` 등 기존 테스트가 깨지지 않는다.

---

## 31. Verification Commands

Python 백엔드 기준 검증 명령:

```bash
python -m pytest backend/app/tests/test_readability.py
python -m pytest backend/app/tests/test_chunker.py
python -m pytest backend/app/tests/test_rag_engine.py
python -m pytest backend/app/tests/test_quiz_generator.py
python -m pytest backend/app/tests/test_content_e2e.py
python -m pytest backend/app/tests/test_extension_session.py
python -m pytest
```

FastAPI 서버가 준비된 이후 (Content Reducer 엔드포인트 테스트):

```bash
uvicorn backend.app.main:app --reload
curl -X POST http://localhost:8000/api/reading-sessions/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1", "document_id": "doc1", "raw_text": "테스트 원문..."}'
```

코드 스타일 도구:

```bash
python -m ruff check backend/app/agents/content_reducer/
python -m ruff format backend/app/agents/content_reducer/
```

Ragas faithfulness 검증 (1차):

```bash
python backend/app/agents/content_reducer/rag_engine.py --eval-mode
```

Git 상태 확인:

```bash
git status
```

---

## 32. Branch Plan

팀 저장소를 사용할 경우 권장 브랜치 구조:

```text
main
├── feature/orchestrator-core       # 1번
├── feature/content-rag             # 2번 (본인)
├── feature/backend-realtime        # 3번
├── feature/frontend-dashboard      # 4번
└── feature/qa-evaluation           # 5번
```

2번 역할 브랜치:

```bash
git checkout -b feature/content-rag
```

통합 브랜치:

```bash
git checkout -b integration/m1-demo
git checkout -b integration/m2-full
```

운영 방식:

- 2번은 `feature/content-rag`에서 readability, chunker, restructurer, rag_engine, quiz_generator를 개발한다.
- M0 직후에는 stub을 1번 `feature/orchestrator-core`에 공유한다.
- M1 직전에는 `integration/m1-demo`에서 1번~4번 작업을 합쳐 데모 흐름을 확인한다.
- M3 이후에는 구조 변경을 금지하고 bugfix만 허용한다.

---

## 33. Development Prompts

### 가독성 분석기 구현 프롬프트

```text
ARCHITECTURE_2.md와 DELIVERY_PLAN_2.md를 참고해서
한국어 텍스트의 가독성 지수를 계산하는 readability.py를 구현해 주세요.

조건:
- 입력: 한국어 텍스트 문자열
- 출력: 0~100 범위의 float difficulty_score
- 평균 어절 수, 한자어/전문용어 비율, 평균 음절 수를 반영하세요.
- 같은 입력이면 항상 같은 출력 (재현 가능한 순수 함수)
- 0~100으로 clamp 처리
- pytest 단위 테스트를 함께 작성하세요.
```

### Semantic Chunker 구현 프롬프트

```text
ARCHITECTURE_2.md의 chunker.py 섹션을 참고해서
의미 단위 청킹 모듈을 구현해 주세요.

조건:
- LangChain SemanticChunker를 기반으로 사용하세요.
- chunk_id 규칙: chunk_{document_id}_{순번(2자리 zero-padding)}
- 각 ChunkDict에 chunk_id, original_text, char_start, char_end, difficulty 포함
- 최소/최대 chunk 크기 제한 적용
- pytest 단위 테스트를 함께 작성하세요.
```

### RAG 용어풀이 엔진 구현 프롬프트

```text
ARCHITECTURE_2.md의 rag_engine.py 섹션을 참고해서
pgvector 기반 RAG 용어풀이 엔진을 구현해 주세요.

조건:
- 입력: 재구성된 chunk 목록
- 출력: 각 chunk에 terms 배열 주입 (term, definition, source, faithfulness_score)
- Vector DB: PostgreSQL + pgvector (환경 변수로 접속 정보 관리)
- RAG는 오직 용어풀이에만 적용하세요.
- Ragas Faithfulness 지표로 생성 결과를 검증하세요.
- Vector DB 실패 시 terms = [] 반환 (fallback)
- pytest 단위 테스트를 함께 작성하세요.
```

### 퀴즈 생성기 구현 프롬프트

```text
ARCHITECTURE_2.md의 quiz_generator.py 섹션을 참고해서
문맥 맞춤형 퀴즈 생성기를 구현해 주세요.

조건:
- 입력: chunk_id (str), context (str, 재구성된 chunk 텍스트)
- 출력: QuizDict (chunk_id, question, options 4개, correct_option 1~4, explanation)
- 오답(distractors)은 그럴듯하지만 명확히 틀린 선택지
- 유효성 검사: 4개 선택지, correct_option 범위, explanation 비어있지 않음
- 유효성 실패 시 fallback 퀴즈 반환
- pytest 단위 테스트를 함께 작성하세요.
```

### Integration Contract 검토 프롬프트

```text
현재 CONTENT_AGENT_CONTRACT.md와 contracts.py를 검토해서
1번/3번/4번/5번 팀원이 실제 구현을 붙일 때 막힐 부분을 찾아 주세요.

검토 기준:
- chunk_id 규칙이 팀 전체에서 일관하게 사용되는가?
- difficulty_score가 0~100으로 정규화되어 있는가?
- terms 배열에 source와 faithfulness_score가 포함되어 있는가?
- 프론트가 chunks/terms로 바로 렌더링할 수 있는가?
- 1번 Orchestrator의 state에 2번 출력이 병합 가능한가?
- 5번 QA가 평가할 수 있는 faithfulness_score와 trace가 있는가?
```

---

## 34. Comparison Criteria for 2번 역할 완료 판단

| Criteria | Question |
|---|---|
| Scope Control | Orchestrator 구현이나 프론트 작업까지 떠안지 않고 콘텐츠 처리 역할에 집중했는가? |
| Contract Clarity | 1번/3번/4번이 JSON 계약만 보고 연결 작업을 할 수 있는가? |
| Readability Reliability | difficulty_score가 같은 입력에서 항상 같은 결과를 내는가? |
| Chunking Consistency | chunk_id가 안정적으로 생성되어 3번 행동 데이터와 매핑 가능한가? |
| RAG Trustworthiness | 용어풀이가 지어낸 내용 없이 출처 기반으로만 생성되었는가? |
| Quiz Relevance | 퀴즈가 해당 chunk 내용과 실제로 관련 있는가? |
| Fallback Stability | 각 서브모듈이 실패해도 데모 전체가 중단되지 않는가? |
| Integration Readiness | stub을 실제 모듈로 교체하기 쉬운 구조인가? |
| Presentation Value | 단순 요약과 무엇이 다른지 구조적으로 설명할 수 있는가? |

---

## 35. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| LLM 재구성 품질 불안정 | 사용자 이해도 저하 | 샘플 텍스트 5개 이상으로 품질 수동 검토 후 출시 |
| pgvector 연동 지연 | RAG 구현 불가 | 3번 백엔드와 pgvector 접속 정보를 M0 직후 협의 |
| 용어집 데이터 부족 | 툴팁 coverage 낮음 | IT 용어 100개 우선 구축, 부족하면 terms = [] fallback |
| Faithfulness 기준 미달 | 환각 내용 포함 위험 | 0.8 미만 시 프롬프트 수정 사이클 반복 |
| chunk_id 불일치 | 행동 데이터 매핑 실패 | M0에서 규칙 확정 후 팀 공유, 변경 금지 |
| LLM 비용 초과 | 개발 비용 증가 | 경량 모델 라우팅 기준 엄격 적용, 테스트 시 stub 사용 |
| 퀴즈 유효성 실패율 높음 | 데모에서 퀴즈 미노출 | fallback 퀴즈 사전 준비 (chunk당 1개씩) |
| 1번과의 계약 불일치 | 통합 실패 | M0에서 계약 확정 후 변경 시 반드시 1번과 협의 |
| 시간이 부족함 | 기능 미완성 | Must Have 우선, Should Have는 후순위 |

---

## 36. Commit Plan

Phase 0 문서 커밋:

```bash
git add ARCHITECTURE_2.md DELIVERY_PLAN_2.md
git commit -m "docs: add content reducer architecture and delivery plan"
```

M0 Stub 커밋:

```bash
git add backend/app/agents/content_reducer/ backend/app/agents/stubs/
git commit -m "feat: add content reducer stub and contracts for orchestrator E2E"
```

M1 콘텐츠 파이프라인 커밋:

```bash
git commit -m "feat: add readability, chunker, restructurer, and rag engine"
```

M2 퀴즈 생성기 및 통합 커밋:

```bash
git commit -m "feat: add quiz generator and integrate content reducer with orchestrator"
```

M3 안정화 커밋:

```bash
git commit -m "fix: stabilize content pipeline and improve faithfulness"
```

---

## 37. Final Checklist

최종 제출 전 2번 역할 확인:

- [x] `2_ARCHITECTURE.md` 작성 완료 (현재 `2/2_ARCHITECTURE.md`로 이동 및 정리 완료)
- [x] `2_DELIVERY_PLAN.md` 작성 완료 (현재 `2/2_DELIVERY_PLAN.md`로 이동 및 정리 완료)
- [x] `contracts.py`에 ContentReducerRequest / ContentReducerResponse 정의
- [x] `content_reducer_stub.py` 구현 및 1번 연결 확인
- [x] `readability.py` 구현 및 테스트 통과
- [x] `chunker.py` 구현 (chunk_id 규칙 포함) 및 테스트 통과
- [x] `restructurer.py` 구현 및 LLM 라우팅 적용
- [x] `prompts.py` 재구성 프롬프트 분리
- [x] `rag_engine.py` 구현 (pgvector 연동, faithfulness 검증)
- [x] `quiz_generator.py` 구현 및 유효성 검사
- [x] `fallbacks.py` 각 서브모듈 fallback 정의
- [x] `agent.py` 에이전트 진입점 (`run_content_reducer`) 구현
- [x] `test_readability.py` 통과
- [x] `test_chunker.py` 통과
- [x] `test_rag_engine.py` 통과
- [x] `test_quiz_generator.py` 통과
- [x] `test_content_e2e.py` 통과
- [x] `docs/CONTENT_AGENT_CONTRACT.md` 작성
- [x] `docs/RAG_ARCHITECTURE.md` 작성
- [x] `docs/QUIZ_DESIGN.md` 작성
- [x] `docs/READABILITY_FORMULA.md` 작성
- [x] 1번 Orchestrator 실제 연결 완료
- [x] 3번 chunk_id 매핑 확인
- [x] 4번 프론트 JSON 형식 확인
- [x] 5번 QA trace/faithfulness_score 전달 확인
- [x] M1 파이프라인 3회 이상 반복 성공
- [x] 확장 인입 라우트(`extension_session.py`) content[] 세션 시작 동작
- [x] PDF 문단 재구성 1차(줄/하이픈/빈줄 분리, `viewer.js`) 동작
- [x] (확장 E1~E2) web/PDF content[] 정규화 동일화 + 반복 머리말/꼬리말 제거
- [x] (확장 E3) 무료 용어풀이 `POST /api/terms/lookup` 구현 (유료 API 미사용)
- [x] (확장 E5) `test_extension_session.py` 확장 케이스 추가 통과
- [x] 7/10 M3 이후 구조 변경 없음 (7/11~7/14 버그 수정·검토만)
- [x] 발표용 RAG 환각 방지 + 확장(웹/PDF 무설치 폴백) 설명 준비

---

## 38. One-line Definition of Done

2번 역할은 다음 문장이 실제 데모와 코드로 증명되면 완료된 것이다.

```text
원문이 사용자의 수준에 맞게 재구성되고,
신뢰 출처 기반의 용어풀이가 환각 없이 제공되며,
집중도 저하 시점에 맞는 퀴즈가 생성되어
Orchestrator를 통해 사용자의 독해 과정에 기여한다.

(확장) 나아가 크롬에서 읽는 웹페이지와 PDF 어느 쪽에서 들어와도
동일한 content[] 계약으로 이 파이프라인이 그대로 동작하고,
단어 용어풀이는 비용 0 경로로 제공된다.
```
