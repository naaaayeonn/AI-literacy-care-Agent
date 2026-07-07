# Content Agent Contract (2번 역할 입출력 계약)

> **대상**: 1번(Orchestrator), 3번(Backend), 4번(Frontend), 5번(QA)  
> **버전**: v0 (M0 기준)  
> **관리**: 2번 역할 (변경 시 팀 전체 공지 필수)

---

## chunk_id 규칙 (팀 전체 필수 준수)

```
형식: chunk_{document_id}_{순번(2자리 zero-padding)}
예시: chunk_doc001_01, chunk_doc001_02, chunk_doc001_10
```

> [!IMPORTANT]
> `chunk_id`는 **3번 행동 데이터**, **4번 UI 하이라이트**, **퀴즈 연결** 모두에서 공통 키로 사용됩니다.  
> M3 이후 절대 형식 변경 금지.

---

## 1. Content Reducer — 원문 처리

### 1.1 요청 (Orchestrator → 2번)

```json
{
  "session_id": "s_2026_001",
  "raw_text": "인공지능의 LLM 레이턴시 최적화 기법 중 하나인 하이브리드 라우팅은...",
  "user_literacy_level": 3,
  "target_domain": "IT/Software",
  "profile": {
    "reading_level": "intermediate",
    "weaknesses": ["long_sentence", "technical_terms"]
  }
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `session_id` | string | ✅ | 세션 식별자 |
| `raw_text` | string | ✅ | 분석할 원문 텍스트 |
| `user_literacy_level` | int (1~5) | ✅ | 사용자 리터러시 수준 |
| `target_domain` | string | ❌ | 도메인 힌트 (e.g., "IT/Software") |
| `profile` | dict | ❌ | 사용자 프로필 |

### 1.2 응답 (2번 → Orchestrator)

```json
{
  "session_id": "s_2026_001",
  "readability_score": 42.3,
  "difficulty_score": 57.7,
  "chunks": [
    {
      "chunk_id": "chunk_doc001_01",
      "original_text": "인공지능의 LLM 레이턴시 최적화 기법 중...",
      "restructured_text": "AI 답변 속도를 높이기 위해 어려운 작업과 쉬운 작업을 나눠 처리하는 방법이 있습니다.",
      "difficulty": 57.7,
      "terms": [
        {
          "term": "레이턴시",
          "definition": "시스템이 요청을 받은 후 응답을 보낼 때까지 걸리는 대기 시간.",
          "source": "도메인 용어집 IT 편",
          "faithfulness_score": 0.96,
          "chunk_id": "chunk_doc001_01"
        }
      ],
      "char_start": 0,
      "char_end": 78
    }
  ],
  "simplified_text": "AI 답변 속도를 높이기 위해...",
  "terms": [
    {
      "term": "레이턴시",
      "definition": "시스템이 요청을 받은 후 응답을 보낼 때까지 걸리는 대기 시간.",
      "source": "도메인 용어집 IT 편",
      "faithfulness_score": 0.96,
      "chunk_id": "chunk_doc001_01"
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `readability_score` | float (0~100) | 높을수록 읽기 쉬움 |
| `difficulty_score` | float (0~100) | 높을수록 어려움. `= 100 - readability_score` |
| `chunks` | list[ChunkDict] | 의미 단위 분할 청크 목록 |
| `chunks[].chunk_id` | string | **chunk_id 규칙 준수 필수** |
| `chunks[].original_text` | string | 원문 청크 |
| `chunks[].restructured_text` | string | LLM 재구성 결과 (M1 이후) |
| `chunks[].difficulty` | float | 청크별 난이도 (0~100) |
| `chunks[].terms` | list | 청크 내 용어풀이 |
| `chunks[].char_start` | int | 원문 내 시작 위치 (프론트 하이라이트용) |
| `chunks[].char_end` | int | 원문 내 종료 위치 |
| `simplified_text` | string | 전체 재구성 텍스트 (프론트 전체보기용) |
| `terms` | list[TermDict] | 세션 전체 용어 (중복 제거) |
| `terms[].faithfulness_score` | float (0~1) | RAG 충실도 점수 (5번 QA용) |

---

## 2. 퀴즈 생성 — 집중도 저하 개입

### 2.1 퀴즈 생성 요청 (Orchestrator → 2번, 3번 트리거 수신 후)

```json
{
  "session_id": "s_2026_001",
  "chunk_id": "chunk_doc001_02",
  "context": "AI 답변 속도를 높이기 위해 어려운 작업과 쉬운 작업을 나눠서 처리하는 방법이 있습니다.",
  "user_literacy_level": 3
}
```

### 2.2 퀴즈 응답 (2번 → Orchestrator)

```json
{
  "chunk_id": "chunk_doc001_02",
  "question": "하이브리드 라우팅의 주요 목적은 무엇인가요?",
  "options": [
    "1. AI 모델의 학습 데이터를 늘리기 위해",
    "2. 어려운 작업과 쉬운 작업을 나눠 AI 답변 속도를 높이기 위해",
    "3. 사용자의 개인정보를 보호하기 위해",
    "4. 텍스트의 글자 수를 줄이기 위해"
  ],
  "correct_option": 2,
  "explanation": "본문에서 하이브리드 라우팅은 AI 답변 속도(레이턴시)를 높이기 위해 복잡한 작업과 단순한 작업을 분리 처리하는 방법이라고 설명합니다."
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `chunk_id` | string | 퀴즈 출처 청크 |
| `question` | string | 문제 |
| `options` | list[string] | 4개 선택지 ("1. ...", "2. ...", "3. ...", "4. ...") |
| `correct_option` | int (1~4) | 정답 번호 (1-indexed) |
| `explanation` | string | 정답 해설 |

---

## 3. Trace 필드 (5번 QA 연동)

Content Reducer가 state의 `trace`에 기록하는 항목:

```json
{
  "step": "content_reducer",
  "status": "success",
  "readability_score": 42.3,
  "difficulty_score": 57.7,
  "chunk_count": 3,
  "term_count": 4,
  "latency_ms": 1842,
  "mode": "real"
}
```

| 필드 | 설명 |
|---|---|
| `step` | 항상 `"content_reducer"` |
| `status` | `"success"` / `"fallback"` / `"stub"` |
| `latency_ms` | 실행 시간 (밀리초) |
| `mode` | `"real"` / `"stub"` |

---

## 4. Fallback 동작 (실패 시)

| 실패 상황 | 동작 |
|---|---|
| 가독성 분석 실패 | `difficulty_score = 50.0` (중간값) |
| 청킹 실패 | 원문 전체를 단일 chunk로 반환 |
| LLM 재구성 실패 | `restructured_text = original_text` |
| RAG 검색 실패 | `terms = []` |
| 퀴즈 생성 실패 | 사전 준비된 기본 퀴즈 반환 |

> [!WARNING]
> fallback 발생 시 trace의 `status`가 `"fallback"`으로 기록됩니다.  
> 5번 QA는 이 값으로 품질 이슈를 감지합니다.
