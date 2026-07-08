# Delivery Plan

## 1. 문서 목적

이 문서는 2026 AI/SW 경진대회 프로젝트에서 **5번 역할: QA / Evaluation & Integration 담당**을 완수하기 위한 개발 실행 계획을 정리한다.

`ARCHITECTURE.md`가 "무엇을 검증할 것인가"를 설명하는 문서라면,

이 문서는

> "언제, 어떤 순서로, 어떤 기준으로 품질을 보장할 것인가"

를 정의한다.

5번 역할의 핵심은 시스템 전체가 정상적으로 동작하고, 품질이 유지되며, 데모가 안정적으로 실행된다는 것을 증명하는 것이다.

---

## 2. 전체 개발 목표

최종 목표는 팀 전체 산출물인 AI 리터러시 케어 데모 안에서 QA와 평가 시스템이 안정적으로 동작하도록 만드는 것이다.

### 최종 산출물

- Golden Dataset
- Unit Test Suite
- Integration Test Suite
- Smoke Test
- Ragas Evaluation Pipeline
- Promptfoo Regression Pipeline
- LangSmith Trace System
- Quality Report
- Deployment Checklist

### 최종적으로 보장해야 하는 흐름

```text
Generated Output
↓
Ragas Evaluation
↓
Promptfoo Regression
↓
Integration Test
↓
Quality Report
↓
Deployment Validation
↓
Demo Ready
```

---

## 3. Scope Definition

### 5번 역할이 책임지는 것

| 영역 | 책임 내용 |
|-------|---------|
| Unit Test | 함수 단위 검증 |
| Integration Test | 전체 흐름 검증 |
| Ragas | Faithfulness, Relevance 평가 |
| Promptfoo | 회귀 테스트 |
| LangSmith | Trace 수집 |
| Quality Report | 평가 결과 생성 |
| Demo Validation | 시연 환경 점검 |
| Deployment Check | 제출 환경 검증 |

---

## 4. Milestone Overview

| Milestone | Date | Goal | 상태 |
|------------|------|------|------|
| M0 | 6/22 | 테스트 환경 구축(기본 pytest) | ✅ 부분(89개 백엔드 테스트 존재) |
| M1 | 6/29 | 핵심 데모 검증(스모크) | 🔄 M1 데모 스모크만 존재(`test_m1_demo_smoke`) |
| M2 | 7/6 | 평가 파이프라인 구축 | ⬜ **미착수**(evaluation/ 미생성) |
| **M3** | **7/10 (금)** | **QA 전 기능 완성 + 기능 동결** | 🔄 진행 예정 — **본 계획의 핵심** |
| 버그 검토 | 7/11~14 | 버그 수정·검토만(신규 금지) | ⬜ 예정 |
| Final | 7/15 (수) | 프로그램 제출 | ⬜ 예정 |

> **일정 원칙**: 7/10까지 아래 §4.5의 남은 QA 산출물을 **전부 완성**한다. 7/11~14는
> 버그 수정·회귀 재검증·데모 리허설만(신규 기능 금지). 7/15 제출.

---

## 4.5 현재 실제 완료 상태 (2026-07-06 기준) — 정직 점검

> 이전 체크리스트와 코드 실제 상태를 대조한 결과. **평가 인프라 대부분이 아직 미구축**이며,
> 이것이 7/10까지의 주 작업량이다.

| 산출물 | 문서상 표기 | 코드 실제 | 판정 |
|---|---|---|---|
| 백엔드 pytest 테스트 | ✅ | `backend/app/tests/` **89개 함수 존재**(1·3번 작성: score/routing/quiz/orchestrator/extension_session 등) | ✅ 기반 확보(5번 회귀 안전망으로 채택) |
| Golden Dataset | ✅ | `golden_dataset/` 폴더 **없음**, json **없음** | ❌ **미구축** |
| Integration/Smoke 스위트(5번 구조) | ⬜ | `test_m1_demo_smoke` 1개만. unit/integration/smoke 분리 구조 없음 | 🔄 부분 |
| Ragas Evaluation | 🔄 | 구현 **없음**(문서 언급만) | ❌ **미구축** |
| Promptfoo Regression | ⬜ | 구현 **없음** | ❌ **미구축** |
| LangSmith Trace | ⬜ | 구현 **없음** | ❌ **미구축** |
| Quality Report | ⬜ | 생성기 **없음**, `reports/` 폴더 없음 | ❌ **미구축** |
| 실제 퀴즈 평가 모듈(3번 인계) | ⬜ | `qa_eval_client` = **no-op 스텁** | ❌ **미구축**(핵심 인계물) |
| 확장 QA(웹/PDF/REST) | — | `test_extension_session.py` 7개 존재(3번 계약), PDF 추출·REST 스모크 없음 | 🔄 부분 |

> **결론**: "완료"로 표기됐던 Golden Dataset·평가 파이프라인은 **실제로는 미착수**다. 아래
> 일자 계획은 이 현실 위에서, 5번이 **다른 모델 완성과 무관하게 먼저 할 수 있는 것(Layer A/B)**을
> 앞당기고, 의존 항목(Layer C)은 컨틴전시를 두고 배치한다(ARCHITECTURE §9).

---

# Phase 0 Goal : 문서와 기준 확정

## 완료 기준

- ARCHITECTURE.md 존재
- DELIVERY_PLAN.md 존재
- 5번 역할의 책임 범위 명확화
- 평가 기준 정의
- 테스트 구조 정의

---

# Phase 1 Goal : M0 테스트 기반 구축

## 완료 기준

- pytest 구조 생성
- tests 폴더 생성
- Golden Dataset 구축
- Unit Test 작성
- Integration Test 작성

### Must Have

| Task | Description | Done When |
|--------|------------|------------|
| Project Scaffold | evaluation, tests 구조 생성 | 폴더 존재 |
| Golden Dataset | 샘플 데이터 구축 | json 파일 존재 |
| Unit Test | test_score, test_router | pytest 통과 |
| Integration Test | E2E 테스트 | flow 테스트 통과 |

### Not Today

- Promptfoo
- Ragas
- LangSmith
- 배포

---

# Phase 2 Goal : M1 핵심 데모 검증

## 완료 기준

- 데모 흐름 검증
- Smoke Test 작성
- LangSmith Trace 연결

### Must Have

#### Ragas Evaluation

평가 항목

- Faithfulness
- Answer Relevance

완료 기준

```text
Faithfulness > 0.8
Answer Relevance > 0.8
```

#### Demo Smoke Test

```text
글 입력
↓
집중도 측정
↓
퀴즈
↓
Literacy Score
↓
그래프
```

#### LangSmith Trace

```text
Content Reducer
↓
Cognitive Care
↓
Reward
↓
Profile
```

호출 기록 저장

---

# Phase 3 Goal : M2 평가 파이프라인 구축

## 완료 기준

- Promptfoo 구축
- Quality Report 생성
- Regression Test 수행

### Must Have

#### Promptfoo

```text
v1
↓
code change
↓
v2
```

성능 저하 감지

#### Quality Report

출력 예시

```json
{
    "passed": true,
    "faithfulness": 0.91,
    "relevance": 0.88,
    "warnings": []
}
```

#### Golden Dataset 확장

20~30개 구축

---

# Phase 4 Goal : M3 기능 동결 및 안정화

## 완료 기준

- Bug Triage
- Regression Recheck
- Demo Repeat 3회 성공

---

# Phase 5 Goal : M4 제출본 검증

## 완료 기준

- Deployment Check
- Final Smoke Test
- Docs Sync

---

# Daily Task Plan — 7/6 → 7/15 (의존성 인지 재계획)

> **레이어 표기**(ARCHITECTURE §9): **A**=5번 단독 가능(남의 완성 무관) · **B**=스텁/목업 대상 검증 ·
> **C**=실제 모듈 도착 필요(컨틴전시 있음). 굵은 날짜가 7/10 기능 프리즈 마감.

| Date | Layer | Task | 완료 기준 | 컨틴전시(미완 시) |
|------|-------|------|-----------|------------------|
| **7/6 (월)** | A | 평가 스캐폴딩 생성 — `backend/evaluation/`·`golden_dataset/`·`reports/` 폴더 + `pyproject/pytest.ini` | 폴더·설정 존재, `pytest` 수집됨 | — (단독) |
| **7/6 (월)** | A | 기존 89개 테스트를 회귀 기반으로 채택 + 전체 green 확인 | `pytest` 전체 통과 스냅샷 | — |
| **7/7 (화)** | A | **Golden Dataset v1** — 웹 본문 5~10개 + **PDF 추출 골든 3~5개**(문단 재구성 기대값) | json 존재, 로드 테스트 통과 | — |
| **7/7 (화)** | B | 확장 인입 스모크 — `/api/session/start`(content[])·`/events`(REST)·`/result` 왕복 | 스텁 경로로 3-스텝 green | 스텁으로 무조건 가능 |
| **7/8 (화)** | A | **PDF 추출 품질 테스트**(`test_pdf_extraction`) — 줄 병합·하이픈·머리말 제거 | 골든 대비 문단 복원율 기준 통과 | pdf.js 추출 로직 미완이면 기대값만 고정, 실측은 도착 시 |
| **7/8 (화)** | A | **REST 이벤트 구동 스모크**(`test_rest_event_flow`) — WS 아님(ADR-001) | events→개입 응답 검증 | — |
| **7/8~9 (수)** | A | **Ragas 하네스 + 무료 폴백** — faithfulness/relevance, judge 없으면 휴리스틱 | 골든에 대해 점수 산출(폴백 포함) | 유료 키 없으면 휴리스틱 자동 폴백(§10) |
| **7/9 (수)** | A | **Promptfoo 회귀 + Quality Report 생성기** — v1↔v2, `unverified` 항목 노출 | `reports/`에 리포트 json 생성 | 스텁 응답 대비로 무료 구동 |
| **7/9 (수)** | A/B | **LangSmith Trace 또는 JSON Trace 폴백** — 에이전트 호출 추적 | trace 기록 저장(무료/로컬) | 무료 티어 초과 시 로컬 JSON |
| **7/9~10 (목)** | C | **실제 퀴즈 평가 모듈**(`quiz_eval.py`) → 3번 `comprehension_score` 인계 | 목업 85 대체, 스텁↔real 토글 | **미완 시 목업 유지 + 리포트에 명시**, 데모 안전 |
| **7/10 (목)** | C | **실 모듈 통합 재검증** — 2번 실제 요약·real cognitive care·확장 실왕복을 골든셋으로 | 도착분 green, 미도착분 unverified 표기 | 도착 안 한 모듈은 스텁 경로로 데모 유지 |
| **7/10 (금)** M3 | — | **기능 동결** — Quality Report 1부 산출 + **데모 3회 연속 성공** | 웹·확장·PDF 3경로 시연 안정 | — |
| 7/11 (금) | — | 버그 수정 — 확장/PDF/REST 경로 회귀 소탕 | 회귀 0 | 신규 기능 금지 |
| 7/12 (토) | — | Regression 재검증 — 골든셋 전체 재실행, unverified 축소 | 리포트 갱신 | |
| 7/13 (일) | — | 시연 리허설 — QA 관점 3경로 점검 | 리허설 통과 | |
| 7/14 (월) | — | **제출본 검증** — Deployment Check·Final Smoke·Docs Sync | 배포 재현 확인 | |
| 7/15 (수) | — | **프로그램 최종 제출** | 제출 완료 | |

---

# 협업·의존 체크포인트 (다른 모델 완성도 추적)

> 5번은 아래 인계물이 **stub→real로 바뀌는 시점**을 추적해 그때마다 재검증한다.

| 대상 | 인계물 | 필요 시점 | 미완 시 5번 대응 |
|---|---|---|---|
| 2번 | 실제 요약/terms API | 7/9~10 | 스텁 content_reducer로 파이프라인 유지, 실측은 unverified |
| 3번 | `/result`가 5번 퀴즈 점수 소비 | 7/9~10 | 목업 85 유지, 인계 계약(`comprehension_score`)만 먼저 확정 |
| 4번 | 확장 오버레이/퀴즈 모달/툴팁 | 7/9~10 | 백엔드 계약만 자동 검증, UI는 수동 체크리스트 분리 |
| 1번 | 오케스트레이터 score/state | 확정됨 | 기존 89 테스트로 회귀 커버 |
| 다른 모델(LLM) | Ragas judge·실제 생성 | 상시 | 무료/오프라인 폴백(§10), 키 있으면 실행 |

---

# Final Checklist (2026-07-06 실제 반영)

- [~] pytest Test Suite — **89개 기반 확보**, 5번 확장 표면 테스트 추가 필요(7/7~8)
- [ ] Golden Dataset 구축 (웹 + **PDF 추출 골든**) — 7/7
- [ ] Integration / Smoke Test (확장 REST 왕복 포함) — 7/7~8
- [ ] Ragas Evaluation Pipeline (무료 폴백 포함) — 7/8~9
- [ ] Promptfoo Regression Pipeline — 7/9
- [ ] LangSmith Trace(또는 JSON Trace 폴백) — 7/9
- [ ] Quality Report 생성 (unverified 항목 노출) — 7/9
- [ ] 실제 퀴즈 평가 모듈 → 3번 인계 (미완 시 목업 유지) — 7/9~10
- [ ] 확장 QA: PDF 추출 품질 · REST 이벤트 구동 스모크 — 7/8
- [ ] Demo 3회 연속 성공 (웹·확장·PDF) — 7/10
- [ ] 제출본 검증 완료 — 7/14

> **정직 원칙**: 미검증 항목은 숨기지 않고 Quality Report에 `unverified`로 노출한다.
> 다른 모델 미완으로 실측이 안 된 부분도 "스텁 기준 통과 / 실 모듈 미검증"으로 구분 기재한다.

---

# One-line Definition of Done

```text
생성 결과의 품질을 정량적으로 평가하고,

코드 변경 후에도 성능 저하 없이,

시스템 전체가 안정적으로 동작함을

테스트와 평가 리포트로 증명할 수 있다.
```
