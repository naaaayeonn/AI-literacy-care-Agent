# AI 리터러시 케어 에이전트 — 2번 역할: Content & RAG Agent

> 2026 AI/SW 경진대회 출품작 | **2번 역할: 콘텐츠 처리 / RAG 기술리드**

## 역할 한 줄 정의

사용자의 인지 수준에 맞게 원문을 재구성하고, 환각 없는 신뢰 출처 기반 용어풀이와 동적 퀴즈를 제공하여 자기주도적 독해를 지원하는 콘텐츠 처리 엔진.

---

## 프로젝트 구조

```
ai-literacy-care-agent/
├── ARCHITECTURE_2.md          # 2번 역할 아키텍처 문서
├── DELIVERY_PLAN_2.md         # 2번 역할 개발 실행 계획
├── requirements.txt
├── .env.example               # 환경 변수 템플릿
├── backend/
│   └── app/
│       ├── agents/
│       │   ├── content_reducer/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py          # 에이전트 진입점
│       │   │   ├── contracts.py      # 입출력 타입 정의
│       │   │   ├── readability.py    # 한국어 가독성 분석
│       │   │   ├── chunker.py        # 의미 단위 청킹
│       │   │   ├── restructurer.py   # LLM 텍스트 재구성
│       │   │   ├── rag_engine.py     # RAG 용어풀이 엔진
│       │   │   ├── quiz_generator.py # 퀴즈 생성기
│       │   │   ├── router.py         # LLM 난이도 라우팅
│       │   │   ├── prompts.py        # 프롬프트 템플릿
│       │   │   └── fallbacks.py      # 서브모듈 실패 처리
│       │   └── stubs/
│       │       ├── __init__.py
│       │       └── content_reducer_stub.py  # E2E 더미 구현
│       └── tests/
│           ├── __init__.py
│           ├── test_readability.py
│           ├── test_chunker.py
│           ├── test_rag_engine.py
│           ├── test_quiz_generator.py
│           └── test_content_e2e.py
├── data/
│   └── term_dictionary.json   # 신뢰 출처 용어집 (RAG 데이터)
└── docs/
    ├── CONTENT_AGENT_CONTRACT.md
    ├── RAG_ARCHITECTURE.md
    ├── QUIZ_DESIGN.md
    └── READABILITY_FORMULA.md
```

---

## 빠른 시작

### 1. 환경 설정

```bash
# 가상 환경 생성 (권장)
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
copy .env.example .env
# .env 파일을 열어 아래 키를 입력합니다:
# - GEMINI_API_KEY: SnowChat API 키 (sookmyung.factchat.bot 개발자 대시보드 발급키)
# - WOORIMAL_API_KEY (선택): 국립국어원 우리말샘 오픈 API 키
# - STDICT_API_KEY (선택): 국립국어원 표준국어대사전 오픈 API 키. 설정 시 표준적 표제어 정의를 우리말샘보다 우선적으로 실시간 매핑합니다.
```

### 2. 데모 모드로 실행 (API 키 없이)

```bash
# .env에서 DEMO_MODE=true 설정
python -m backend.app.agents.content_reducer.agent
```

### 3. 실제 모드로 실행 (Gemini 기반)

```bash
# .env에서 GEMINI_API_KEY 설정 후
python -m backend.app.agents.content_reducer.agent
```

---

## 테스트 실행

```bash
# 전체 테스트 (총 97개 테스트 100% Green 패스 완료)
python -m pytest backend/app/tests/ -v

# 단위 테스트만
python -m pytest backend/app/tests/test_readability.py -v
python -m pytest backend/app/tests/test_chunker.py -v

# 확장 세션 테스트만
python -m pytest backend/app/tests/test_extension_session.py -v

# E2E 테스트
python -m pytest backend/app/tests/test_content_e2e.py -v
```

---

## 핵심 설계 원칙

| 원칙 | 내용 |
|---|---|
| **Stub First** | 실제 LLM 없이 1번 Orchestrator E2E 흐름을 먼저 지원 |
| **RAG 범위 제한** | RAG는 용어풀이에만 적용. 요약/재구성에 미적용 |
| **환각 차단** | 모든 용어풀이는 신뢰 출처 데이터 기반 (직접 인용 방식, faithfulness_score=1.0) |
| **Fallback 보장** | 각 서브모듈 실패 시 기본값 반환으로 데모 유지 |
| **chunk_id 안정성** | 같은 문서는 항상 같은 chunk_id 생성 |
| **비용 0원 원칙** | 교내 생성형 AI 플랫폼 SnowChat의 `gemini-2.5-flash` 게이트웨이 모델을 활용하여 요금 차단 |
| **동적 퀴즈 개입** | 3번 WebSocket 연동 시 Redis 세션 상태 기반으로 읽기 진행도에 매칭되는 dynamic 퀴즈 생성 |


---

## 제공 API 엔드포인트 명세

### 1. 콘텐츠 가독성 요약 및 가공
* **`POST /api/content-reducer/reduce`** (Orchestrator용 표준 경로)
* **`POST /api/session/start`** (크롬 확장 프로그램 / PDF 전용 인입 경로)
  * 문단 정규화 및 페이지 반복 머리말/꼬리말 제거 알고리즘 탑재
  * Frontend 호환성을 지원하기 위해 **camelCase 및 snake_case 이중 필드 호환 매핑** 반환

### 2. 특정 문맥 기반 독해 퀴즈 생성
* **`POST /api/content-reducer/quiz`**
  * 청크의 재구성 문맥을 기반으로 4지선다형 퀴즈 및 해설 생성 (실패 시 Fallback 퀴즈 작동)

### 3. 실시간 Hover 단어 무료 조회
* **`POST /api/terms/lookup`**
  * 크롬 확장 프로그램에서 hover된 단어의 용어풀이를 비용 없이 조회 (정확 매칭 + 임베딩 코사인 유사도)
  * 드래그한 문맥의 `anchorNode.parentElement` 텍스트 기반 300자 추출 전처리로 LLM 동음이의어(Disambiguation) 판별률 극대화

> 전체 계약 명세: [`docs/CONTENT_AGENT_CONTRACT.md`](docs/CONTENT_AGENT_CONTRACT.md)

---

## Milestone 현황

| Milestone | 날짜 | 상태 |
|---|---|---|
| M0 | 6/22 | ✅ Stub E2E 및 계약 초안 완료 |
| M1 | 6/29 | ✅ 핵심 파이프라인(가독성·청킹·RAG·재구성) 완료 |
| M2 | 7/6  | ✅ 퀴즈 생성 및 Orchestrator 통합 완료 |
| **ME** | 7/6~7/9 | ✅ 크롬 확장 및 PDF 대응 인입/Header/Footer 제거/Lookup 완료 |
| M3 | 7/10 | ✅ 기능 동결 및 Gemini API 완전 마이그레이션 완료 |
| M4 | 7/14 | ✅ 최종 제출본 점검, 표준국어대사전 API 통합 및 3번 실시간 개입 퀴즈 버그 픽스 완료 |
