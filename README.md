# AI Literacy Care Agent

> **AI가 글을 대신 읽어주는 서비스가 아니라, 사용자의 문해력 성장을 관리하는 서비스**

읽기 행동과 이해도를 측정하고, 실시간 개입을 통해 사용자의 문해력 향상을 돕는 **폐루프(Closed-Loop) 멀티 에이전트 시스템**

---

## 📌 Overview

AI Literacy Care Agent는 사용자가 텍스트를 읽는 **과정(Process)** 과 **결과(Outcome)** 를 함께 분석하여 문해력 성장을 지속적으로 관리하는 개인 맞춤형 AI 서비스

기존 생성형 AI가 텍스트를 요약하는 데 초점을 맞춘다면, 본 시스템은 다음을 수행

* 사용자가 실제로 읽고 있는지 측정
* 내용을 이해했는지 검증
* 문해력이 향상되고 있는지 추적
* 개인별 맞춤 개입 및 학습 경로 제공

---

## 🎯 Problem Statement

최근 긴 글을 읽고 이해하는 능력은 지속적으로 감소

* 한국 PIAAC 언어능력 점수 273점(2012) → 249점(2023) 감소 
* 숏폼 콘텐츠 확산으로 인한 집중력 저하
* ADHD·난독증 사용자를 위한 한국어 지원 서비스 부족
* 기존 AI 서비스는 사용자의 성장 여부를 관리하지 못함 

---

## 💡 Key Idea

### GPT는 텍스트를 처리하고, 우리는 사람을 관리한다.

본 서비스는 **측정 → 개입 → 추적**의 폐루프 구조를 통해 사용자의 문해력 성장을 지속적으로 관리

```text
Measure
   ↓
Intervene
   ↓
Track
   ↓
Personalization
   ↺
```

---

## ✨ Key Features

### 📖 Adaptive Reading

* Semantic Chunking
* 난이도 분석
* 쉬운 문장 재구성
* 전문 용어 설명(RAG)

### 🧠 Cognitive Care

* 스크롤 속도 분석
* 체류 시간 측정
* 페이지 이탈 감지
* 실시간 집중도 평가

### 🔔 Adaptive Nudge

집중도가 낮아질 경우 3단계 개입을 수행

| Level  | Intervention        |
| ------ | ------------------- |
| Soft   | 핵심 문장 강조, 가독성 개선    |
| Medium | 다시 읽기를 유도하는 텍스트 가이드 |
| Hard   | 즉석 퀴즈를 통한 재집중       |

### 🎮 Gamification

* 경험치
* 배지
* 레벨 시스템
* 성장 리포트

### 📈 Dynamic Literacy Profile

장기 데이터를 기반으로

* 취약 영역 분석
* 개인화 학습 경로 추천
* 지속적인 난이도 조정

을 수행합니다. 

---

## 📊 Literacy Score

본 프로젝트의 핵심 지표

```text
Literacy Score
=
f(
    Comprehension,
    Engagement,
    Difficulty Adjustment
)
```

### Components

#### 1. Comprehension

* 퀴즈 정답률
* 텍스트 난이도 보정

#### 2. Engagement

* 스크롤 속도
* 체류 시간
* 이탈률

#### 3. Cross Validation

* 비정상적인 읽기 패턴 감지
* 찍기 방지

#### 4. Longitudinal Analysis

* 단일 세션이 아닌 시계열 기반 성장 추적

---

## 🏗 Architecture

시스템은 LangGraph 기반의 계층형 멀티 에이전트 구조로 설계

```text
User
 ↓
Main Orchestrator
 ↓
├── Content Reducer
├── Cognitive Care
├── Reward Agent
├── Literacy Profile Agent
└── QA / Evaluation Agent
```

---

## 🤖 Agents

### 1. Main Orchestrator

* 상태 관리
* 동적 워크플로우 제어
* 결과 검증

### 2. Content Reducer

* 난이도 분석
* Semantic Chunking
* 쉬운 문장 변환
* RAG 기반 용어 설명

### 3. Cognitive Care Agent

* 행동 데이터 수집
* 집중도 분석
* 적응형 넛지 제공

### 4. Reward Agent

* 경험치
* 배지
* 성장 피드백

### 5. Literacy Profile Agent

* 사용자 프로파일링
* 개인화 학습 경로 생성

### 6. QA / Evaluation Agent

* 회귀 테스트
* 품질 평가
* 버그 탐지

---

## 🛠 Tech Stack

### Backend

* Python 3.11
* FastAPI
* WebSocket
* Async Processing

### Database

* PostgreSQL
* Redis

### Multi-Agent Framework

* LangGraph
* StateGraph
* LangChain
* SemanticChunker

### LLM

* Claude (Opus / Sonnet)
* GPT-4o
* Lightweight Models

### Evaluation

* Promptfoo
* Ragas
* LangSmith



---

## 📚 RAG

RAG는 전체 시스템에 적용하지 않고, **Content Reducer의 용어 풀이 기능에만 제한적으로 사용**

Grounding Sources

* 표준국어대사전
* 전문 용어집
* 위키 기반 지식

이를 통해 환각(Hallucination)을 줄이고 Faithfulness를 향상

---

## 🧪 Evaluation

2단계 검증 구조를 적용

### Runtime Quality

* Self-Correction
* Faithfulness
* Quiz Relevance

### Product QA

* Unit Test
* Integration Test
* Regression Test

### Metrics

* Faithfulness
* Answer Relevance
* Readability Score
* Latency
* Token Cost
* User Engagement
* Completion Rate

---

## 🖥 User Interface

### Adaptive Reading Interface

* Smart Highlighting
* Contextual Tooltips
* Interactive Quiz

### Personalized Growth Dashboard

* Literacy Score 변화 그래프
* 주간·월간 집중도 통계
* 레벨 및 배지 시스템

### Browser Extension

웹 페이지 위에 직접 개입하는 Overlay 형태로 동작

---

## 🚀 Roadmap

### Phase 1

* 행동 데이터 수집
* WebSocket 구축
* LangGraph 기반 구조 설계

### Phase 2

* 집중도 측정
* Adaptive Nudge
* Quiz
* Literacy Score

### Phase 3

* RAG
* 콘텐츠 재구성
* 게이미피케이션

### Phase 4

* QA / Evaluation
* Harness Engineering
* Demo



---

## 🎯 Target Users

### 2030 세대

긴 글 집중력 저하 및 숏폼 콘텐츠 의존 문제 해결

### 학습자 및 취업 준비생

논문·기사·보고서 등의 고난도 텍스트 이해 지원

### ADHD · 난독증 사용자

한국어 기반 AI 주석 및 집중 관리 기능 제공



---

## 📌 Vision

> ChatGPT는 한 번 읽고 잊지만,
>
> **AI Literacy Care Agent는 사용자가 어떻게 읽는지 측정하고, 이해했는지 검증하며, 나아지는지를 지속적으로 추적**

사용자가 텍스트를 소비하는 것을 넘어,

**스스로 읽고 이해하며 성장할 수 있도록 돕는 개인 맞춤형 문해력 성장 관리 시스템**을 지향


---

# AI Literacy Care Backend

본 저장소는 2026 AI/SW 경진대회 프로젝트의 **3번 역할(Cognitive Care Agent 및 실시간 데이터 파이프라인)** 코드를 담고 있습니다.

## 🚀 빠른 시작 가이드 (Quick Start)

백엔드를 실행하기 위해 로컬에 Python을 직접 설치할 필요가 없습니다. Docker만 설치되어 있다면 단 한 줄의 명령어로 DB, Redis, 서버가 모두 실행됩니다.

1. **저장소를 클론합니다.**
   ```bash
   git clone https://github.com/naaaayeonn/AI-literacy-care-Agent.git
   cd AI-literacy-care-Agent
   git checkout feature/backend
   ```

2. **도커를 실행합니다.**
   ```bash
   docker-compose up -d --build
   ```

3. **서버 확인**
   - 백엔드 API 명세서 (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
   - 정상 가동 중이라면 위 링크에서 `/api/sessions/start` 와 `/api/sessions/{session_id}/finish` API를 테스트할 수 있습니다.

## 🔌 프론트엔드 연동 정보
- **REST API Base URL**: `http://localhost:8000`
- **WebSocket Endpoint**: `ws://localhost:8000/ws/session/{session_id}`

### 세션 시작 (Start Session)
`POST /api/sessions/start`
```json
{
  "user_id": "user_123",
  "document_id": "doc_abc"
}
```
**응답 (Response)**: `session_id` 발급

### 실시간 데이터 전송 (WebSocket)
프론트엔드에서 사용자가 글을 읽는 동안, 아래와 같은 JSON을 웹소켓으로 지속적으로 보냅니다.
```json
{
  "events": [
    {"type": "scroll", "timestamp_ms": 1700000000, "position": 0.45},
    {"type": "blur", "duration_ms": 3000}
  ]
}
```

### 세션 종료 및 점수 저장 (Finish Session)
`POST /api/sessions/{session_id}/finish`
- 웹소켓 연결 종료 후 호출합니다. Redis에 쌓였던 로그가 DB로 영구 저장됩니다.
