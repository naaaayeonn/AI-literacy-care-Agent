# RAG 아키텍처 문서

> **문서 목적**: 2번 역할의 RAG 파이프라인 설계를 설명한다.  
> 발표 시 "환각 방지 방법" 질문에 대한 기술적 근거로 활용한다.

---

## 1. 핵심 설계 원칙

> [!IMPORTANT]
> **RAG는 오직 용어풀이에만 적용한다.**  
> 텍스트 재구성/요약에는 RAG를 절대 적용하지 않는다.  
> RAG를 재구성에 적용하면 환각이 아닌 부분에도 검색 결과가 섞여 원문 의미가 변질될 수 있다.

| 모듈 | RAG 적용 | 이유 |
|---|---|---|
| 가독성 분석 (readability.py) | ❌ | 규칙 기반 순수 함수 |
| 텍스트 재구성 (restructurer.py) | ❌ | LLM 자체 능력 활용, RAG 혼입 시 의미 변질 |
| **용어풀이 (rag_engine.py)** | **✅** | 신뢰 출처 검색으로 환각 원천 차단 |
| 퀴즈 생성 (quiz_generator.py) | ❌ | chunk 원문 기반, 외부 검색 불필요 |

---

## 2. 전체 RAG 파이프라인 흐름

```
                    ┌─────────────────────────────────────┐
                    │         원문 청크 입력                │
                    │  (restructured_text or original_text)│
                    └─────────────────┬───────────────────┘
                                      │
                          ┌───────────▼──────────────┐
                          │   용어 후보 추출           │
                          │  (keyword matching)        │
                          └───────────┬──────────────┘
                                      │
              ┌───────────────────────▼─────────────────────┐
              │              용어집 검색                      │
              │         term_dictionary.json                  │
              │  (신뢰 출처: TTA, 표준국어대사전 등)          │
              └───────────────────────┬─────────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │     Faithfulness 계산               │
                    │  (검색 결과 = 출처 데이터 → 1.0)    │
                    └─────────────────┬──────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │        TermDict 반환                 │
                    │  term, definition, source,           │
                    │  faithfulness_score, chunk_id        │
                    └────────────────────────────────────┘
```

---

## 3. 환각 방지 메커니즘

### 왜 환각이 발생하는가?

LLM은 용어를 스스로 설명할 때 학습 데이터에 없는 정보를 그럴듯하게 생성한다. 이를 환각(Hallucination)이라고 하며, 교육 맥락에서 특히 위험하다.

### 이 시스템의 환각 차단 방법

| 방법 | 설명 |
|---|---|
| **생성이 아닌 검색** | LLM이 용어를 만들지 않고, 사전에 검증된 용어집에서 검색 |
| **신뢰 출처 명시** | 모든 용어풀이에 출처 (TTA, 표준국어대사전 등) 포함 |
| **Faithfulness 점수** | 검색 결과와 출처의 일치도를 수치로 측정 (0~1) |
| **임계값 경고** | faithfulness < 0.8이면 trace에 경고 기록 |

---

## 4. 기술 스택 (M1 기준)

| 구성요소 | M1 구현 | M2+ 업그레이드 |
|---|---|---|
| 용어 저장소 | JSON 파일 (`term_dictionary.json`) | PostgreSQL + pgvector |
| 검색 방법 | 키워드 매칭 (regex) | 임베딩 코사인 유사도 |
| 임베딩 모델 | (선택적) sentence-transformers | `jhgan/ko-sroberta-multitask` |
| Faithfulness | 토큰 중복 기반 근사 | Ragas Faithfulness 지표 |

---

## 5. 용어집 데이터 구조

```json
{
  "term": "LLM",
  "aliases": ["대규모 언어 모델", "Large Language Model"],
  "definition": "방대한 텍스트 데이터를 학습하여 인간과 유사한 언어를 이해하고 생성하는 딥러닝 모델.",
  "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
  "domain": "IT"
}
```

| 필드 | 설명 |
|---|---|
| `term` | 대표 용어명 (검색 키) |
| `aliases` | 별칭 목록 (영어, 한자 등) |
| `definition` | 신뢰 출처 기반 풀이 |
| `source` | 출처 기관명 |
| `domain` | 도메인 분류 (IT / 교육 / 언어) |

현재 용어집: **25개** (M1 기준)  
목표: 100개 이상 (M2~M3 단계적 추가)

---

## 6. pgvector 업그레이드 계획

M2 이후 실제 서버 환경에서 pgvector로 전환 시:

```sql
-- PostgreSQL + pgvector 테이블 구조
CREATE TABLE term_embeddings (
    id          SERIAL PRIMARY KEY,
    term        TEXT NOT NULL,
    definition  TEXT NOT NULL,
    source      TEXT NOT NULL,
    domain      TEXT,
    embedding   vector(768),  -- ko-sroberta-multitask 차원
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON term_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

전환 방법:
1. `.env`에서 `RAG_MODE=pgvector` 설정
2. `rag_engine.py`의 pgvector 모드 활성화
3. 기존 JSON 용어집 데이터를 임베딩하여 DB에 삽입

---

## 7. Faithfulness 점수 해석

| 점수 | 의미 | 대응 |
|---|---|---|
| 1.0 | 출처 데이터와 완전 일치 | 정상 |
| 0.8 ~ 0.99 | 높은 충실도 | 정상 |
| 0.5 ~ 0.79 | 중간 충실도 | trace 경고 기록 |
| 0.5 미만 | 낮은 충실도 | 해당 용어 제외 검토 |

> [!NOTE]
> M1에서는 용어집에서 직접 가져온 정의를 사용하므로 faithfulness_score = 1.0.  
> pgvector 전환 후 유사도 기반 검색 시 점수가 달라질 수 있다.
