# Delivery Plan

> **진행 현황 범례 (2026-07-05 기준)** — 각 표의 `상태` 열과 체크박스로 구분한다.
> - ✅ **완료** — 구현·검증됨(테스트/실서버 확인)
> - 🔄 **진행/부분** — 구조는 있으나 마무리·연결 남음
> - ⬜ **미완료** — 아직 착수 안 함(주로 M3 이후·제출 단계)
>
> **한 줄 요약:** 코어 폐루프(M0·M1)와 계약·점수·통합 구조·3번 real 연결·확장 글루(REST alias·pdf.js·익명 UUID)까지 **완료**.
> 남은 것은 **2번 Content Reducer real 연결 + 확장 웹/PDF 실통합·수동 E2E**.
>
> **목표 일정 (개정):** 남은 작업 + 확장 추가 작업을 **7/10(금)까지 모두 완성 → 모델 전체 완성·기능 동결**.
> **7/11(토)~7/14(화)는 버그 수정·검토만**(신규 기능·구조 변경 금지), **7/15(수) 제출**. 상세는 §4-1·§27 참조.

## 1. 문서 목적

이 문서는 2026 AI/SW 경진대회 프로젝트에서 **1번 역할: 에이전트 코어 / 오케스트레이션 기술리드**를 완수하기 위한 개발 실행 계획을 정리한다.

`ARCHITECTURE.md`가 "무엇을 어떤 구조로 만들 것인가"를 설명하는 문서라면, 이 문서는 "언제, 어떤 순서로, 어디까지 구현할 것인가"를 정의한다.

1번 역할의 핵심은 앱 전체를 혼자 완성하는 것이 아니라, 팀원들이 만든 서브 에이전트와 프론트/백엔드 기능을 하나의 폐루프 시스템으로 연결하는 것이다.

---

## 2. 전체 개발 목표

최종 목표는 팀 전체 산출물인 AI 리터러시 케어 데모 안에서 1번 역할이 담당하는 코어 시스템을 안정적으로 동작시키는 것이다.

1번 역할의 최종 산출물:

- Shared State 스키마
- 에이전트 입출력 계약
- Main Orchestrator 실행 흐름
- 조건부 라우팅 로직
- Literacy Score 계산 엔진
- Stub 기반 E2E 데모
- 실제 팀원 모듈과 연결 가능한 adapter/client 구조
- trace/error/fallback 구조
- 핵심 단위 테스트
- 통합 체크리스트

최종 데모에서 1번 역할이 보장해야 하는 흐름:

```text
원문 입력
→ Content Reducer 호출
→ 읽기 행동 이벤트 수집
→ Cognitive Care 호출
→ 집중도 기반 개입 판단
→ 퀴즈 결과 반영
→ Literacy Score 계산
→ Reward 호출
→ Literacy Profile 업데이트
→ 프론트에 최종 결과 JSON 반환
```

---

## 3. Scope Definition

### 1번 역할이 책임지는 것

| 영역 | 책임 내용 |
|---|---|
| Shared State | 모든 에이전트가 공유하는 세션 상태 구조 정의 |
| Agent Contract | 각 팀원이 구현할 에이전트의 입력/출력 JSON 계약 정의 |
| Orchestrator Flow | 에이전트 실행 순서와 상태 전이 흐름 구현 |
| Routing Logic | 집중도, 퀴즈, 상태에 따라 개입 수준 결정 |
| Score Engine | 이해도, 집중도, 난이도, 교차검증을 합친 Literacy Score 계산 |
| Stub E2E | 실제 에이전트 없이도 전체 흐름이 돌아가는 더미 구현 |
| Integration | stub을 실제 팀원 모듈로 교체할 수 있는 구조 제공 |
| Trace / Fallback | 실패 지점 추적, 에이전트 실패 시 기본값 처리 |
| Core Test | score, routing, state, orchestrator flow 단위 테스트 |

### 1번 역할이 직접 책임지지 않는 것

| 영역 | 주 담당 | 1번의 관여 |
|---|---|---|
| 쉬운 문장 변환 | 2번 콘텐츠/RAG | 입력/출력 계약 정의 |
| RAG 용어풀이 | 2번 콘텐츠/RAG | terms 출력 구조 정의 |
| WebSocket 행동 데이터 수집 | 3번 백엔드 | event schema 정의 |
| DB/Redis 상세 구현 | 3번 백엔드 | 저장해야 할 state 필드 협의 |
| 읽기 화면 UI | 4번 프론트 | 응답 JSON 정의 |
| 그래프/대시보드 UI | 4번 프론트 | score/trend 데이터 제공 |
| Ragas/Promptfoo 파이프라인 | 5번 QA | trace/generated output 제공 |

---

## 4. Milestone Overview

| 상태 | Milestone | Date | Goal | Done When |
|---|---|---:|---|---|
| ✅ | M0 | 6/22 | 프로젝트 코어 골격과 더미 E2E 통신 | raw_text 입력 후 더미 결과 JSON 반환 |
| ✅ | M1 | 6/29 | 핵심 폐루프 데모 완성 | 측정 → 개입 → 점수 계산 흐름 동작 |
| 🔄 | M2 | 7/6 | 전 기능 통합(웹 경로) | 실제 팀원 모듈 연결(3번 완료, **2번 real 연결**) |
| ⬜ | **M3** | **7/10** | **★모델 전체 완성 · 기능 동결** | 코어 실모듈 연결 + **확장 웹+PDF 전 기능 실동작**, 이후 구조 변경 없음 |
| ⬜ | 버그 수정 | 7/11~7/14 | 버그 수정·검토만 | 신규 기능/구조 변경 없이 안정화·리허설 |
| ⬜ | Final | 7/15 | 프로그램 제출 | 팀 최종 산출물 제출 |

---

## 4-1. 남은 작업 & 확장 추가 작업 (7/10까지 완성)

> 이미 완료한 부분(§6~§26·§37의 ✅)을 제외하고, **7/10 모델 전체 완성**을 위해 남은 작업과
> 확장 추가 작업만 모은 실행 백로그. 각 항목의 목표 완료일을 함께 표기한다.

### (A) 남은 코어 작업

| 상태 | 작업 | 완료 기준 | 목표일 |
|---|---|---|---|
| ⬜ | **2번 Content Reducer real 연결** | `LITERACY_CONTENT_IMPL=real`로 실모듈 chunks/simplified/terms/difficulty가 state에 merge, 데모 정상 | 7/6 |
| 🔄 | 시계열 추세 산출 마무리 | previous_scores→trend(improving/stable/declining) 반환·그래프 데이터 제공 | 7/9 |
| 🔄 | 점수 보정 튜닝 | 가독성 정규화·교차검증 감점 실데이터 기준 조정 | 7/9 |
| ⬜ | 전 기능 통합 회귀 | content→care→routing→score→reward→profile 실모듈 경로 pytest 통과 | 7/9 |

### (B) 확장 추가 작업 (1번 담당분)

> 확장 설계·계약·글루의 **대부분은 완료**(REST alias·shared 공용화·pdf.js 뷰어·익명 UUID 스키마).
> 남은 것은 **실브라우저 통합 검증**과 **웹/PDF 왕복 E2E**다.

| 상태 | 작업 | 완료 기준 | 목표일 |
|---|---|---|---|
| ✅ | 확장 인입 alias(`/session/start`·`/events`·`/result`) | 코어 재사용, content[]·REST 개입·result 반환 | (완료) |
| ✅ | shared 공용화(tracker/overlay/session_client) | 웹·PDF 동일 모듈 재사용 | (완료) |
| ✅ | pdf.js 자체 뷰어 + 텍스트 추출 | PDF 링크 리다이렉트→렌더→content[] | (완료) |
| ✅ | 익명 UUID·consent 상태 스키마 + userId 계약 정합 | 로그인 없이 프로필 누적 | (완료) |
| ⬜ | 확장 크롬 로드 → **웹 수동 E2E 왕복** | ON→기사 읽기→넛지/개입 오버레이 동작 확인 | 7/7 |
| ⬜ | **PDF 왕복 E2E**(pdf.js) | PDF 링크→뷰어 전환→스크롤/개입 동작 확인 | 7/8 |
| 🔄 | 확장↔백엔드 이벤트 스키마 최종 정합(G6) | 확장이 보내는 이벤트가 백엔드 계약과 일치 | 7/7 |
| ⬜ | 온보딩/식별 연동 확인 | 팝업 동의→익명 UUID 발급→세션 userId 반영 | 7/8 |

### (C) 협업 대기 (타 역할, 1번은 계약 제공)

| 담당 | 작업 | 1번 관여 |
|---|---|---|
| 2번 | pdf.js/Readability → 동일 content[] 정규화, RAG 용어풀이(무료) | 계약 제공·검증 |
| 4번 | 팝업 온보딩 UI, 단어 툴팁, 퀴즈 모달, 성장 대시보드, WS→flush POST | 이벤트·개입 JSON 계약 제공 |
| 5번 | 확장 수동 브라우저 E2E, Ragas/Promptfoo 회귀 | 시나리오·trace 제공 |

---

## 5. Phase 0 Goal: 문서와 기준 확정

Phase 0에서는 구현보다 기준 확정을 우선한다. 1번 역할은 다른 팀원들이 병렬 개발할 수 있도록 공통 계약을 먼저 정해야 한다.

## Phase 0 완료 기준

- `ARCHITECTURE.md`가 존재한다.
- `DELIVERY_PLAN.md`가 존재한다.
- 1번 역할의 책임 범위가 명확하다.
- 팀원별 입력/출력 계약 초안이 있다.
- Shared State 초안이 있다.
- 최소 데모 흐름이 정의되어 있다.

---

## 6. Phase 0 Must Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ✅ | Architecture document | 1번 역할 중심 아키텍처 문서 작성 | `ARCHITECTURE.md` 존재 |
| ✅ | Delivery plan | 구현 순서와 완료 기준 작성 | `DELIVERY_PLAN.md` 존재 |
| ✅ | Role boundary | 1번이 할 일/안 할 일 구분 | 문서에 Scope Definition 포함 |
| ✅ | Core flow | 폐루프 흐름 정의 | `raw_text → score → profile` 흐름 설명 가능 |
| ✅ | Agent contract draft | 팀원별 입출력 계약 초안 | JSON 예시가 문서에 있음 |

---

## 7. Phase 0 Should Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ✅ | Initial folder | 프로젝트 폴더 생성 | `ai-literacy-care-agent/` 존재 |
| ✅ | Docs folder plan | 추가 문서 위치 정의 | `docs/` 구조가 계획에 있음 |
| ✅ | Test plan draft | 테스트 대상 정의 | score/routing/state 테스트 항목 존재 |

---

## 8. Phase 0 Not Today

Phase 0에서는 아래를 구현하지 않는다.

- 실제 LangGraph 구현
- 실제 LLM API 호출
- 실제 RAG 구현
- 실제 WebSocket 구현
- 실제 DB/Redis 연동
- 프론트엔드 UI 구현
- QA 파이프라인 구현
- 배포

---

## 9. Phase 1 Goal: M0 코어 베이스 구현

Phase 1의 목표는 6/22까지 **실제 AI 없이도 전체 흐름이 한 번 도는 코어 베이스**를 만드는 것이다.

이 단계에서는 정교한 기능보다 "연결 가능한 구조"가 중요하다.

## Phase 1 완료 기준

- Python 프로젝트 기본 구조가 있다.
- `ReadingSessionState` 타입이 정의되어 있다.
- stub agent가 있다.
- Orchestrator가 stub agent를 순서대로 호출한다.
- Literacy Score v0가 계산된다.
- 최종 결과 JSON이 반환된다.
- 최소 단위 테스트가 있다.

---

## 10. Phase 1 Must Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ✅ | Project scaffold | 백엔드 코어 폴더 생성 | `backend/app/orchestrator/` 존재 |
| ✅ | Shared State v0 | 세션 상태 타입 정의 | `state.py`에 `ReadingSessionState` 존재 |
| ✅ | Agent stubs | 더미 에이전트 작성 | content/care/reward/profile stub 존재 |
| ✅ | Orchestrator v0 | stub 호출 흐름 구현 | `run_reading_session(state)` 실행 가능 |
| ✅ | Score v0 | 기본 점수 계산 함수 | quiz/focus/difficulty로 score 계산 |
| ✅ | Result JSON | 프론트 전달용 결과 형식 | literacy_score 포함 JSON 반환 |
| ✅ | Basic tests | 핵심 함수 테스트 | score와 flow 테스트 통과 |

---

## 11. Phase 1 Should Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ✅ | API contract doc | 팀원별 JSON 계약 문서 | `docs/API_CONTRACT.md` 존재 |
| ✅ | Shared state doc | state 필드 설명 문서 | `docs/SHARED_STATE.md` 존재 |
| ✅ | Score formula doc | 점수 계산식 설명 | `docs/SCORE_FORMULA.md` 존재 |
| ✅ | Trace v0 | 단계별 실행 로그 | state에 `trace` 누적 |
| ✅ | Fallback v0 | 에이전트 실패 기본값 | stub 실패 시 기본 결과 반환 |

---

## 12. Phase 1 Not Today

Phase 1에서는 아래 기능을 구현하지 않는다.

- LangGraph 고급 분기
- 실제 Claude/GPT 호출
- 실제 RAG 검색
- 실제 DB 저장
- 실제 Redis 세션 캐시
- WebSocket 스트리밍
- 복잡한 시계열 분석
- 관리자 QA 화면

---

## 13. Phase 2 Goal: M1 핵심 폐루프 데모

Phase 2의 목표는 6/29까지 프로젝트의 차별점을 보여주는 최소 폐루프를 완성하는 것이다.

핵심은 "ChatGPT 요약이 아니라, 사용자의 읽기 과정을 측정하고 개입하며 점수화한다"는 것을 데모로 증명하는 것이다.

## Phase 2 완료 기준

- 글 1편 기준 데모가 실행된다.
- 읽기 행동 이벤트가 state에 반영된다.
- focus_score에 따라 intervention이 결정된다.
- quiz_result가 score에 반영된다.
- Literacy Score와 score_breakdown이 반환된다.
- 프론트가 사용할 수 있는 intervention JSON이 반환된다.

---

## 14. Phase 2 Must Have

| 상태 | Task | Related Requirement | Done When |
|---|---|---|---|
| ✅ | Reading event schema | 행동 데이터 계약 | scroll/pause/blur/focus 이벤트 구조 확정 |
| ✅ | Cognitive routing | 집중도 기반 개입 | focus_score에 따라 none/soft/medium/hard 결정 |
| ✅ | Intervention command | 프론트 UI 명령 | `intervention.type`, `level`, `message` 반환 |
| ✅ | Quiz result integration | 이해도 반영 | correct_count/total_count가 score에 반영 |
| ✅ | Score breakdown | 점수 근거 제공 | comprehension/engagement/difficulty/penalty 출력 |
| ✅ | E2E demo data | 샘플 글 1편 | 반복 가능한 데모 입력 데이터 존재 |
| ✅ | M1 smoke test | 핵심 흐름 검증 | 한 명령으로 flow 테스트 가능 |

---

## 15. Phase 2 Should Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ✅ | Abnormal reading penalty | 비정상 읽기 감점 | 빠른 스크롤/탭 이탈 감점 적용 |
| 🔄 | Chunk-level evidence | 어떤 문단에서 집중 저하인지 표시 | `low_dwell_chunks` 같은 evidence 제공 |
| ✅ | Frontend response sample | 프론트용 응답 샘플 | JSON 예시 공유 |
| ✅ | Manual demo script | 시연 순서 문서화 | 3분 안에 설명 가능한 시나리오 존재 |
| ✅ | Error trace | 실패 지점 추적 | trace에 step/status/error 기록 |

---

## 16. Phase 2 Not Today

Phase 2에서는 아래를 후순위로 둔다.

- 완성도 높은 UI
- 실제 브라우저 확장 프로그램
- 장기 사용자 데이터 기반 추천
- 정교한 개인화 알고리즘
- 비용 최적화 LLM 라우팅
- 복잡한 QA 리포트

---

## 17. Phase 3 Goal: M2 실제 모듈 통합

Phase 3의 목표는 7/6까지 stub 기반 코어를 실제 팀원 모듈과 연결하는 것이다.

이 시점부터 1번 역할은 구현자이면서 통합 담당자다. 각 팀원의 결과물이 계약을 지키는지 확인하고, 필요한 경우 adapter를 작성한다.

## Phase 3 완료 기준

- 2번 Content Reducer 결과를 Orchestrator에 연결한다.
- 3번 행동 데이터 또는 focus_score 결과를 연결한다.
- 4번 프론트가 intervention/score JSON을 사용할 수 있다.
- 5번 QA가 trace/generated output을 받을 수 있다.
- stub과 실제 구현을 설정으로 교체할 수 있다.

---

## 18. Phase 3 Must Have

| 상태 | Task | Related Module | Done When |
|---|---|---|---|
| 🔄 | Content adapter | 2번 Content Reducer | 실제 output을 state에 merge 가능 *(구조·토글 준비 완료, 실모듈 연결 남음)* |
| ✅ | Care adapter | 3번 Cognitive Care | focus_score/intervention_needed 수신 가능 *(real 연결·캘리브레이션 완료)* |
| ✅ | Front response contract | 4번 Frontend | 프론트가 score/intervention을 렌더링 가능 |
| ✅ | QA trace export | 5번 QA | trace와 generated_outputs 전달 가능 |
| ✅ | Stub toggle | Integration | stub/real 모듈 전환 가능 |
| ✅ | Integration checklist | Team coordination | 팀원별 연결 상태 확인 가능 |

---

## 19. Phase 3 Should Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ✅ | Profile trend v0 | 이전 점수 대비 추세 | improving/stable/declining 반환 |
| ✅ | Self-correction v0 | 결과 품질 검토 루프 | 비정상 score 또는 빈 output 경고 |
| 🔄 | Latency log | 실행 시간 측정 | trace에 latency_ms 기록 |
| ✅ | Contract validation | 입력/출력 검증 | 필수 필드 누락 시 명확한 error |
| ✅ | Integration tests | 실제 모듈 일부 포함 테스트 | 주요 path 테스트 통과 |

---

## 20. Phase 3 Not Today

Phase 3에서는 아래를 무리해서 넣지 않는다.

- 모든 에이전트의 완전한 실제 구현 연결
- 완전 자동 QA 게이트
- 운영 수준의 인증/인가
- 대규모 사용자 동시 처리
- 고급 추천 알고리즘
- 실제 배포 인프라 최적화

---

## 21. Phase 4 Goal: M3 기능 동결과 안정화

Phase 4의 목표는 7/10까지 구조 변경을 멈추고, 데모가 깨지지 않게 안정화하는 것이다.

## Phase 4 완료 기준

- 기능 추가보다 버그 수정만 진행한다.
- 핵심 데모 시나리오가 반복 실행된다.
- fallback이 정상 동작한다.
- score 계산 근거가 발표에서 설명 가능하다.
- trace를 통해 실패 원인을 확인할 수 있다.

---

## 22. Phase 4 Must Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ⬜ | Freeze core contract | API/state 변경 중단 | 팀원에게 최종 계약 공지 *(M3 미도달)* |
| ⬜ | Bug triage | 통합 오류 우선순위 정리 | 치명/중요/경미 구분 |
| ✅ | Fallback hardening | 실패 시 데모 유지 | 에이전트 실패해도 결과 반환 |
| ✅ | Score sanity check | 점수 비정상값 방지 | 0~100 clamp, NaN 방지 |
| 🔄 | Demo regression | 반복 실행 확인 | 같은 시나리오 3회 이상 성공 *(M1 흐름 반복 확인, M3 정식 회귀는 남음)* |

---

## 23. Phase 4 Should Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ⬜ | Cost/latency note | 발표용 기술 근거 | 고난도만 LLM 사용한다는 설명 가능 |
| 🔄 | QA result hook | QA 결과 연결 | qa_result를 trace 또는 admin data로 확인 |
| 🔄 | Final architecture update | 문서 최신화 | 실제 구현과 문서 차이 반영 *(대부분 동기화, 최종 점검 남음)* |
| ⬜ | Demo fallback data | 비상용 샘플 결과 | API 실패 시 사용할 JSON 준비 |

---

## 24. Phase 4 Not Today

Phase 4에서는 아래 변경을 하지 않는다.

- Shared State 대규모 변경
- 에이전트 계약 변경
- 점수 계산식 전면 교체
- UI 구조 재설계
- DB 구조 대규모 변경
- 새로운 기능 추가

---

## 25. Phase 5 Goal: M4 제출본 점검

Phase 5의 목표는 7/14까지 제출 가능한 상태를 확인하고, 1번 역할의 코어 흐름을 발표에서 설명할 수 있게 준비하는 것이다.

## Phase 5 완료 기준

- 최종 데모 플로우가 안정적이다.
- 발표자가 폐루프 구조를 설명할 수 있다.
- 심사 질문에 대한 기술 방어 근거가 있다.
- 제출본에서 코어 기능이 누락되지 않는다.

---

## 26. Phase 5 Must Have

| 상태 | Task | Description | Done When |
|---|---|---|---|
| ⬜ | Final demo rehearsal | 코어 흐름 리허설 | 측정→개입→점수→프로필 설명 가능 |
| ⬜ | Submission check | 제출본 점검 | 누락 파일/환경 변수 확인 |
| 🔄 | Defense script | 심사 질문 대비 | ChatGPT와 차별점 답변 준비 *(기획서 Q&A로 초안 확보)* |
| ⬜ | Final smoke test | 최종 실행 확인 | 제출 전 데모 흐름 성공 |
| 🔄 | Docs sync | 문서와 구현 일치 | ARCHITECTURE/DELIVERY_PLAN 최신화 |

---

## 27. 1번 역할 Daily Task Plan

| 상태 | Date | Goal | Must Finish |
|---|---|---|---|
| ✅ | 6/20 | 프로젝트 골격 | 폴더 구조, state/graph/score/routing 파일 생성 |
| ✅ | 6/21 | Shared State 확정 | `ReadingSessionState`, event, quiz, score 타입 정의 |
| ✅ | 6/22 | M0 더미 E2E | stub agent와 orchestrator v0 실행 |
| ✅ | 6/23 | 상태 전이 | agent 호출 순서와 trace 기록 |
| ✅ | 6/24 | 라우팅 | focus_score 기반 intervention 결정 |
| ✅ | 6/25 | 퀴즈 연결 | quiz_result를 comprehension_score에 반영 |
| ✅ | 6/26 | Score v1 | Literacy Score 계산식과 breakdown 구현 |
| ✅ | 6/27 | E2E 점검 | 샘플 글 기준 전체 흐름 테스트 |
| ✅ | 6/28 | M1 준비 | 데모 데이터와 fallback 정리 |
| ✅ | 6/29 | M1 완료 | 핵심 폐루프 데모 성공 |
| ✅ | 6/30 | Profile 연동 | 이전 점수/현재 점수 비교 구조 |
| ✅ | 7/1 | Self-Correction | 비정상 결과 감지와 warning 구조 |
| ✅ | 7/2 | 최소 작업 | 코드 리뷰, 문서 업데이트 |
| ✅ | 7/3 | 최소 작업 | 시계열 설계 메모, 계약 변경 반영 |
| ✅ | 7/4 | 최소 작업 | 테스트 케이스 보강 |
| 🔄 | 7/5(일) | 통합 착수 | **2번 Content Reducer real adapter** 연결 착수 + 확장 웹경로 점검 |
| 🔄 | 7/6(월) M2 | 코어 통합 완료 | 2번 real 연결 완료 · 웹 전 기능 통합 디버깅 |
| ⬜ | 7/7(화) | 확장 웹 통합 | 크롬 로드 → **웹 수동 E2E 왕복** · 이벤트 스키마 정합(G6) |
| ⬜ | 7/8(수) | 확장 PDF 통합 | **pdf.js 왕복 E2E** · 온보딩/익명 UUID 연동 확인 |
| ⬜ | 7/9(목) | 마무리·회귀 | 시계열·프로필·리워드 실연결 마무리 · self-correction · 전체 회귀 |
| ⬜ | **7/10(금) M3** | **★모델 전체 완성** | 코어+확장(웹·PDF) 전 기능 실동작 확인 → **기능 동결** |
| ⬜ | 7/11(토) | 버그 수정 | 구조 변경 없이 버그 수정·검토만 |
| ⬜ | 7/12(일) | 버그 수정 | 버그 수정·검토 · 데모 데이터 고정 |
| ⬜ | 7/13(월) | 버그 수정 | 버그 수정·검토 · 시연 리허설(코어 흐름) |
| ⬜ | 7/14(화) | 제출 점검 | 버그 수정 마감 · 제출본 동작 점검 |
| ⬜ | 7/15(수) | 제출 | 프로그램 최종 제출 |

> **개정 요지:** 원래 7/7~7/10에 흩어져 있던 통합·안정화를 앞당겨, **7/10까지 코어(2번 real)와
> 확장(웹+PDF 실통합·E2E)을 모두 완성**한다. 7/10 이후(7/11~14)는 **버그 수정·검토만** 하고,
> 7/15에 제출한다. M4(제출본 점검)는 7/14 버그 수정 구간에 흡수했다.

---

## 28. Manual QA for M0

M0 종료 전 확인할 항목:

- [x] `ai-literacy-care-agent/` 폴더가 있다.
- [x] `ARCHITECTURE.md`가 있다.
- [x] `DELIVERY_PLAN.md`가 있다.
- [x] `state.py`에 핵심 state 타입이 있다.
- [x] stub agent가 있다.
- [x] orchestrator flow가 stub을 호출한다.
- [x] raw_text 입력으로 최종 JSON이 나온다.
- [x] literacy_score 필드가 존재한다.
- [x] trace 필드가 존재한다.
- [x] score 계산 테스트가 있다.

---

## 29. Manual QA for M1

M1 종료 전 확인할 항목:

- [x] 샘플 글 1편으로 데모가 실행된다.
- [x] reading_events가 state에 누적된다.
- [x] focus_score가 계산되거나 입력된다.
- [x] focus_score에 따라 intervention level이 결정된다.
- [x] quiz_result가 score에 반영된다.
- [x] score_breakdown이 반환된다.
- [x] 프론트가 사용할 intervention JSON이 있다.
- [x] 에이전트 실패 시 fallback이 동작한다.
- [x] 데모 흐름을 3회 반복해도 실패하지 않는다.

---

## 30. Manual QA for M2

M2 종료 전 확인할 항목:

- [ ] 2번 Content Reducer 실제 출력과 연결된다. ⬜ **← 남은 작업**
- [x] 3번 행동 데이터 또는 focus_score와 연결된다.
- [x] 4번 프론트가 score/intervention을 표시할 수 있다.
- [x] 5번 QA가 trace를 받을 수 있다.
- [x] stub/real 모듈 전환 방식이 있다.
- [x] 계약과 다른 응답이 들어오면 명확한 오류가 난다.
- [x] 핵심 통합 테스트가 통과한다.

---

## 31. Verification Commands

초기 Python 백엔드 기준 검증 명령:

```bash
python -m pytest
python -m pytest backend/app/tests/test_score.py
python -m pytest backend/app/tests/test_orchestrator_flow.py
```

FastAPI 서버가 준비된 이후:

```bash
uvicorn backend.app.main:app --reload
```

코드 스타일 도구를 쓰는 경우:

```bash
python -m ruff check .
python -m ruff format .
```

Git 상태 확인:

```bash
git status
```

프로젝트에 패키지 매니저가 정해지기 전까지는 위 명령을 기준으로 한다. 팀이 `poetry`, `uv`, `pipenv` 중 하나를 선택하면 명령을 업데이트한다.

---

## 32. Branch Plan

팀 저장소를 사용할 경우 권장 브랜치 구조:

```text
main
├── feature/orchestrator-core
├── feature/content-rag
├── feature/backend-realtime
├── feature/frontend-dashboard
└── feature/qa-evaluation
```

1번 역할 브랜치:

```bash
git checkout -b feature/orchestrator-core
```

통합 브랜치:

```bash
git checkout -b integration/m1-demo
```

운영 방식:

- 1번은 `feature/orchestrator-core`에서 state, graph, score, routing을 만든다.
- M1 직전에는 `integration/m1-demo`에서 2번~4번 작업을 합쳐 데모 흐름을 확인한다.
- M3 이후에는 구조 변경을 금지하고 bugfix만 허용한다.

---

## 33. Development Prompts

### Shared State 설계 프롬프트

```text
ARCHITECTURE.md와 DELIVERY_PLAN.md를 참고해서
1번 역할의 Shared State v0를 설계해 주세요.

조건:
- 앱 전체 구현이 아니라 orchestrator에 필요한 state만 정의하세요.
- Content Reducer, Cognitive Care, Reward, Literacy Profile, QA가 읽고 쓰는 필드를 구분하세요.
- Python TypedDict 또는 Pydantic 중 하나를 선택하고 이유를 설명하세요.
- 아직 실제 LLM 호출, DB 연동, WebSocket 구현은 하지 마세요.
- 구현 전 생성/수정할 파일 목록과 순서를 먼저 제안하세요.
```

### Orchestrator Stub 구현 프롬프트

```text
ARCHITECTURE.md와 DELIVERY_PLAN.md를 참고해서
stub 기반 orchestrator v0를 구현해 주세요.

조건:
- 실제 AI API를 호출하지 마세요.
- content, care, reward, profile은 stub 함수로 만드세요.
- raw_text 입력부터 literacy_score 출력까지 E2E 흐름이 돌아야 합니다.
- 각 단계는 trace에 기록하세요.
- score 계산은 별도 score.py 순수 함수로 분리하세요.
- 구현 후 실행 방법과 테스트 방법을 요약해 주세요.
```

### Score Engine 구현 프롬프트

```text
Literacy Score v1을 구현해 주세요.

조건:
- 입력은 quiz_result, focus_score, difficulty_score, reading_events입니다.
- comprehension_score, engagement_score, difficulty_score, cross_validation_penalty를 분리해서 계산하세요.
- 최종 literacy_score는 0~100으로 clamp하세요.
- 점수 근거를 score_breakdown으로 반환하세요.
- NaN, total_count=0, 누락 필드 같은 예외를 처리하세요.
- pytest 단위 테스트를 함께 작성하세요.
```

### Integration Contract 검토 프롬프트

```text
현재 API_CONTRACT.md와 state.py를 검토해서
2번~5번 팀원이 실제 구현을 붙일 때 막힐 부분을 찾아 주세요.

검토 기준:
- 필수 필드가 빠져 있지 않은가?
- 프론트가 바로 렌더링할 수 있는 응답인가?
- 백엔드가 저장하기 쉬운 구조인가?
- QA가 평가할 수 있는 trace/generated output이 있는가?
- scope가 1번 역할을 벗어나지 않는가?
```

---

## 34. Comparison Criteria for 1번 역할 완료 판단

| Criteria | Question |
|---|---|
| Scope Control | 앱 전체 구현까지 떠안지 않고 코어 역할에 집중했는가? |
| Contract Clarity | 팀원들이 입출력 JSON만 보고 구현할 수 있는가? |
| State Consistency | 모든 에이전트가 같은 Shared State 기준으로 연결되는가? |
| Orchestrator Reliability | 한 에이전트 실패가 전체 데모 중단으로 이어지지 않는가? |
| Score Explainability | Literacy Score가 왜 그 값인지 설명 가능한가? |
| Demo Readiness | M1 데모에서 측정→개입→점수 흐름을 보여줄 수 있는가? |
| Testability | score/routing/flow를 테스트로 검증할 수 있는가? |
| Integration Readiness | stub을 실제 팀원 모듈로 교체하기 쉬운가? |
| Presentation Value | ChatGPT와 차별점을 구조적으로 설명할 수 있는가? |

---

## 35. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| 1번이 앱 전체를 떠안음 | 일정 지연, 역할 붕괴 | Scope Definition을 기준으로 코어만 담당 |
| Shared State가 늦게 정해짐 | 팀원 병렬 개발 불가 | 6/21까지 state v0 확정 |
| 에이전트 계약이 자주 바뀜 | 통합 지연 | M3 이후 계약 변경 금지 |
| LangGraph를 너무 일찍 복잡하게 씀 | 구현 시간 증가 | Python 함수 flow 먼저, 이후 LangGraph 전환 |
| Score 계산이 LLM 의존적임 | 재현성 부족 | score.py 순수 함수로 구현 |
| 프론트가 필요한 응답이 없음 | 데모 화면 연결 실패 | intervention/score/trend JSON을 일찍 공유 |
| 실제 모듈 통합 실패 | M2 지연 | stub fallback 유지 |
| 행동 데이터가 부족함 | 집중도 계산 불안정 | 데모용 mock reading_events 준비 |
| 시간이 부족함 | 기능 미완성 | Must Have 우선, Should Have는 후순위 |

---

## 36. Commit Plan

Phase 0 문서 커밋:

```bash
git add ai-literacy-care-agent/ARCHITECTURE.md ai-literacy-care-agent/DELIVERY_PLAN.md
git commit -m "docs: add orchestrator architecture and delivery plan"
```

M0 코어 베이스 커밋:

```bash
git add ai-literacy-care-agent
git commit -m "feat: add orchestrator core scaffold and stub flow"
```

M1 폐루프 데모 커밋:

```bash
git commit -m "feat: add closed-loop demo flow"
```

M2 통합 커밋:

```bash
git commit -m "feat: integrate orchestrator with team modules"
```

M3 안정화 커밋:

```bash
git commit -m "fix: stabilize orchestrator demo flow"
```

---

## 37. Final Checklist

최종 제출 전 1번 역할 확인:

- [x] `ARCHITECTURE.md` 작성 완료
- [x] `DELIVERY_PLAN.md` 작성 완료
- [x] `ReadingSessionState` 정의
- [x] 에이전트별 입력/출력 계약 정의
- [x] stub 기반 E2E 구현
- [x] Orchestrator flow 구현
- [x] Routing logic 구현
- [x] Literacy Score v1 구현
- [x] score_breakdown 제공
- [x] trace/error/fallback 구조 구현
- [x] 프론트용 intervention/score JSON 제공
- [ ] 2번 Content Reducer 연결 ⬜ **← 남은 작업**
- [x] 3번 Cognitive Care 또는 행동 데이터 연결
- [x] 4번 프론트 응답 연결
- [x] 5번 QA trace 연결
- [x] 핵심 단위 테스트 작성
- [x] M1 데모 3회 이상 반복 성공
- [ ] M3 이후 구조 변경 없음 ⬜ *(M3=7/10 목표)*
- [ ] 발표용 폐루프 설명 준비 🔄 *(기획서 초안 확보, 리허설 남음)*

**확장 추가 (Chrome Extension / PDF)**

- [x] 확장 인입 alias(`/session/start`·`/events`·`/result`) 코어 재사용
- [x] shared 공용화(tracker/overlay/session_client) — 웹·PDF 동일
- [x] pdf.js 자체 뷰어 + 텍스트 추출(content[])
- [x] 익명 UUID·consent 상태 스키마 + userId 계약 정합
- [x] REST(event-driven) 전송 확정(ADR-001) · 비용 0 원칙(ADR-002)
- [ ] 확장 크롬 로드 → 웹 수동 E2E 왕복 ⬜ *(7/7 목표)*
- [ ] PDF 왕복 E2E(pdf.js) ⬜ *(7/8 목표)*
- [ ] 확장↔백엔드 이벤트 스키마 최종 정합(G6) 🔄 *(7/7 목표)*

---

## 38. One-line Definition of Done

1번 역할은 다음 문장이 실제 데모와 코드로 증명되면 완료된 것이다.

```text
사용자의 읽기 행동과 퀴즈 결과가 Shared State에 누적되고,
Orchestrator가 에이전트들을 순서대로 호출하며,
Literacy Score와 개입 결과를 계산해 프론트에 반환한다.
```
