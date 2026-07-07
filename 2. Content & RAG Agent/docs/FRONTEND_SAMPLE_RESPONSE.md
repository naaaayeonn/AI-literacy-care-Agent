# 프론트엔드 응답 샘플 (4번 팀원 공유용)

> **대상**: 4번 프론트엔드 담당  
> **목적**: Content Reducer API 응답의 실제 JSON 구조를 미리 공유하여 UI 구현을 지원한다.

---

## 1. 세션 시작 응답 — 원문 처리 결과

```json
{
  "session_id": "s_2026_demo_001",
  "readability_score": 38.5,
  "difficulty_score": 61.5,
  "simplified_text": "AI와 LLM 시스템은 빠른 응답 속도를 위해 RAG 구조를 씁니다.\n\n이 방법은 AI가 잘못된 정보를 만들어 내는 문제를 줄여줍니다.\n\n메타인지와 글 읽는 능력은 혼자 공부할 때 매우 중요합니다.",
  "chunks": [
    {
      "chunk_id": "chunk_doc_demo_01",
      "original_text": "인공지능(AI)과 LLM 기반 시스템은 레이턴시 최적화를 위해 RAG 아키텍처를 활용한다.",
      "restructured_text": "AI와 LLM 시스템은 빠른 응답 속도를 위해 RAG 구조를 씁니다.",
      "difficulty": 65.2,
      "char_start": 0,
      "char_end": 82,
      "terms": [
        {
          "term": "인공지능",
          "definition": "인간의 학습, 추론, 문제 해결 능력을 컴퓨터가 모방할 수 있도록 만든 기술의 총칭.",
          "source": "표준국어대사전",
          "faithfulness_score": 1.0,
          "chunk_id": "chunk_doc_demo_01"
        },
        {
          "term": "LLM",
          "definition": "방대한 텍스트 데이터를 학습하여 인간과 유사한 언어를 이해하고 생성하는 딥러닝 모델.",
          "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
          "faithfulness_score": 1.0,
          "chunk_id": "chunk_doc_demo_01"
        },
        {
          "term": "레이턴시",
          "definition": "시스템이 요청을 받은 후 응답을 보낼 때까지 걸리는 대기 시간 또는 지연 시간.",
          "source": "도메인 용어집 IT 편",
          "faithfulness_score": 1.0,
          "chunk_id": "chunk_doc_demo_01"
        }
      ]
    },
    {
      "chunk_id": "chunk_doc_demo_02",
      "original_text": "전통적인 학습 환경에서는 인지부하를 고려하지 않은 채 동일한 교육 자료를 모든 학생에게 제공해 왔다.",
      "restructured_text": "예전 학교에서는 뇌의 부담을 생각하지 않고, 모든 학생에게 같은 자료를 나눠줬습니다.",
      "difficulty": 48.7,
      "char_start": 82,
      "char_end": 185,
      "terms": [
        {
          "term": "인지부하",
          "definition": "특정 과제를 수행할 때 인간의 작업 기억에 가해지는 처리 부담의 총량.",
          "source": "교육심리학 용어사전",
          "faithfulness_score": 1.0,
          "chunk_id": "chunk_doc_demo_02"
        }
      ]
    },
    {
      "chunk_id": "chunk_doc_demo_03",
      "original_text": "AI 리터러시 케어 시스템은 자연어 처리(NLP) 기술을 활용하여 텍스트의 가독성을 분석하고, 학습자의 수준에 맞게 내용을 재구성한다.",
      "restructured_text": "AI 학습 도우미는 글을 얼마나 쉽게 읽을 수 있는지 분석하고, 공부하는 사람의 수준에 맞게 내용을 다시 써줍니다.",
      "difficulty": 55.3,
      "char_start": 185,
      "char_end": 320,
      "terms": [
        {
          "term": "자연어 처리",
          "definition": "컴퓨터가 인간의 언어를 이해, 해석, 생성할 수 있게 하는 인공지능의 한 분야.",
          "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
          "faithfulness_score": 1.0,
          "chunk_id": "chunk_doc_demo_03"
        },
        {
          "term": "가독성",
          "definition": "텍스트가 얼마나 쉽고 명확하게 읽힐 수 있는지를 나타내는 지표.",
          "source": "언어학 용어사전",
          "faithfulness_score": 1.0,
          "chunk_id": "chunk_doc_demo_03"
        }
      ]
    }
  ],
  "terms": [
    {
      "term": "인공지능",
      "definition": "인간의 학습, 추론, 문제 해결 능력을 컴퓨터가 모방할 수 있도록 만든 기술의 총칭.",
      "source": "표준국어대사전",
      "faithfulness_score": 1.0,
      "chunk_id": "chunk_doc_demo_01"
    },
    {
      "term": "LLM",
      "definition": "방대한 텍스트 데이터를 학습하여 인간과 유사한 언어를 이해하고 생성하는 딥러닝 모델.",
      "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
      "faithfulness_score": 1.0,
      "chunk_id": "chunk_doc_demo_01"
    },
    {
      "term": "레이턴시",
      "definition": "시스템이 요청을 받은 후 응답을 보낼 때까지 걸리는 대기 시간.",
      "source": "도메인 용어집 IT 편",
      "faithfulness_score": 1.0,
      "chunk_id": "chunk_doc_demo_01"
    },
    {
      "term": "인지부하",
      "definition": "특정 과제를 수행할 때 인간의 작업 기억에 가해지는 처리 부담의 총량.",
      "source": "교육심리학 용어사전",
      "faithfulness_score": 1.0,
      "chunk_id": "chunk_doc_demo_02"
    },
    {
      "term": "자연어 처리",
      "definition": "컴퓨터가 인간의 언어를 이해, 해석, 생성할 수 있게 하는 인공지능의 한 분야.",
      "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
      "faithfulness_score": 1.0,
      "chunk_id": "chunk_doc_demo_03"
    },
    {
      "term": "가독성",
      "definition": "텍스트가 얼마나 쉽고 명확하게 읽힐 수 있는지를 나타내는 지표.",
      "source": "언어학 용어사전",
      "faithfulness_score": 1.0,
      "chunk_id": "chunk_doc_demo_03"
    }
  ]
}
```

---

## 2. 퀴즈 생성 응답 (M2 이후)

집중도 저하 트리거 수신 후 Orchestrator가 2번에 퀴즈를 요청할 때의 응답:

```json
{
  "chunk_id": "chunk_doc_demo_01",
  "question": "이 문단에서 AI와 LLM 시스템이 RAG 구조를 사용하는 주된 이유는 무엇인가요?",
  "options": [
    "1. 더 많은 데이터를 학습하기 위해",
    "2. 빠른 응답 속도(레이턴시)를 위해",
    "3. 사용자의 개인정보를 보호하기 위해",
    "4. 프로그래밍 비용을 줄이기 위해"
  ],
  "correct_option": 2,
  "explanation": "본문에서 AI와 LLM 시스템은 '레이턴시 최적화', 즉 응답 속도를 높이기 위해 RAG 아키텍처를 활용한다고 설명합니다."
}
```

---

## 3. UI 구현 참고 사항

### 읽기 화면

| 데이터 | UI 활용 방법 |
|---|---|
| `chunks[].restructured_text` | 메인 읽기 텍스트로 표시 |
| `chunks[].original_text` | "원문 보기" 토글 버튼으로 제공 |
| `chunks[].char_start ~ char_end` | 원문 하이라이트 위치 계산용 |
| `chunks[].difficulty` | 청크별 난이도 색상 표시 (선택) |

### 용어 툴팁

| 데이터 | UI 활용 방법 |
|---|---|
| `terms[].term` | 텍스트 내 용어 하이라이트 |
| `terms[].definition` | 툴팁 내용 |
| `terms[].source` | 출처 표시 (신뢰성 강조) |
| `terms[].faithfulness_score` | (선택) 품질 배지 표시 |

### 퀴즈 카드

| 데이터 | UI 활용 방법 |
|---|---|
| `quiz.question` | 문제 텍스트 |
| `quiz.options` | 4개 선택지 버튼 |
| `quiz.correct_option` | 정답 확인 (제출 후 표시) |
| `quiz.explanation` | 해설 표시 (정답 후 표시) |

---

## 4. chunk_id 활용 (3번 백엔드 연동)

3번 백엔드는 사용자가 읽고 있는 chunk를 `chunk_id`로 식별하여 행동 데이터를 수집한다.

```json
// 3번이 전송하는 읽기 이벤트 예시
{
  "session_id": "s_2026_demo_001",
  "chunk_id": "chunk_doc_demo_02",  // ← 2번이 정의한 chunk_id 사용
  "event_type": "scroll_pause",
  "duration_ms": 8500,
  "timestamp": "2026-06-29T14:23:11Z"
}
```

> [!IMPORTANT]
> `chunk_id`는 2번이 생성하고, 3번(행동 수집), 4번(UI 하이라이트), 퀴즈 생성 모두에서 공통으로 사용됩니다.  
> 형식 변경 시 반드시 팀 전체에 공지하세요.
