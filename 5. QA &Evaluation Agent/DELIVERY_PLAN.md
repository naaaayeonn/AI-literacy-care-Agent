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

### 직접 책임지지 않는 것

| 영역 | 담당 |
|------|------|
| Content Reducer 구현 | 2번 |
| Focus Score 계산 | 3번 |
| UI 구현 | 4번 |
| Orchestrator 구현 | 1번 |

---

## 4. Milestone Overview

| Milestone | Date | Goal |
|------------|------|------|
| M0 | 6/22 | 테스트 환경 구축 |
| M1 | 6/29 | 핵심 데모 검증 |
| M2 | 7/6 | 평가 파이프라인 구축 |
| M3 | 7/10 | 안정화 |
| M4 | 7/14 | 제출본 검증 |
| Final | 7/15 | 프로그램 제출 |

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

# Daily Task Plan

| Date | Goal |
|------|------|
| 6/20 | pytest 구조 생성 |
| 6/21 | Golden Dataset 구축 |
| 6/22 | E2E 더미 통신 테스트 |
| 6/23 | Unit Test 작성 |
| 6/24 | 행동 데이터 검증 |
| 6/25 | Ragas Relevance 평가 |
| 6/26 | 점수 정합성 테스트 |
| 6/27~28 | Integration Test |
| 6/29 | M1 Demo Validation |
| 6/30 | Promptfoo 구축 |
| 7/1 | Faithfulness 측정 |
| 7/2~4 | Golden Dataset 보강 |
| 7/5 | Regression Test |
| 7/6 | M2 통합 점검 |
| 7/7 | 통합 테스트 주도 |
| 7/8~9 | Bug Triage |
| 7/10 | 기능 동결 |
| 7/11~12 | Regression 재검증 |
| 7/13 | 시연 리허설 |
| 7/14 | 제출본 검증 |
| 7/15 | 프로그램 제출 |

---

# Final Checklist

- [ ] Golden Dataset 구축
- [ ] pytest Test Suite 작성
- [ ] Integration Test 작성
- [ ] Smoke Test 작성
- [ ] Ragas Evaluation Pipeline 구축
- [ ] Promptfoo Regression Pipeline 구축
- [ ] LangSmith Trace 구축
- [ ] Quality Report 생성
- [ ] Demo 3회 연속 성공
- [ ] 제출본 검증 완료

---

# One-line Definition of Done

```text
생성 결과의 품질을 정량적으로 평가하고,

코드 변경 후에도 성능 저하 없이,

시스템 전체가 안정적으로 동작함을

테스트와 평가 리포트로 증명할 수 있다.
```
