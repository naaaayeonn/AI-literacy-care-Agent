# [통합] content_reducer 임시 브릿지 안내 + 2번 실구현 교체 요청 (Claude→Gemini 무료)

> from 1번(오케스트레이션) · 2026-07-06 · 관련: `FEEDBACK_TO_ROLE2_FROM_ROLE1.md`, 기획서 §2-5

안녕하세요 2번! 폐루프 데모가 지금 돌아가야 해서 `content_reducer`를 **임시 브릿지**로 붙였습니다.
**2번 실구현이 오면 바로 교체**할 거라, 아래 **계약만 맞춰주시면** 됩니다.

---

## 1. 지금 상태 — 임시 브릿지 (1번이 붙임, 곧 폐기 예정)

`backend/app/agents/content_reducer_client.py`의 `_REAL_IMPL`을 임시 오프라인 어댑터로 연결했습니다.

| 필드 | 임시 브릿지 방식 |
|---|---|
| `chunks` / `difficulty_score` | 오프라인 결정론 청킹 (의존성·API 없음) |
| `terms` | `term_dictionary.json` 사전 **검색**(키워드 매칭) |
| `simplified_text` | **Gemini 무료** 재구성, 실패 시 원문 passthrough 폴백 |

→ 데모 방어용 임시본입니다. **2번 real 도착 시 이 브릿지는 폐기**합니다.

---

## 2. 2번이 최종적으로 해줄 것 — 진입점 하나로 노출

저장소 `2. Content & RAG Agent/`의 real 파이프라인을 완성해서 **아래 한 함수**로 노출해주세요.
1번은 이 시그니처로만 호출합니다(어댑터가 이걸 `_REAL_IMPL`에 연결).

```python
def run_content_reducer(state) -> state:
    """raw_text를 읽어 아래 4개 필드를 state에 채운다."""
```

**채워야 할 필드 (snake_case · ReadingSessionState 계약):**

| 필드 | 타입 | 내용 |
|---|---|---|
| `chunks` | `list[dict]` | `{chunk_id, text, summary, difficulty}` (+ 있으면 `char_start`/`char_end` → 프론트 하이라이트용) |
| `simplified_text` | `str` | 쉬운문장 재구성 결과 |
| `terms` | `list[TermDict]` | 용어풀이(2번 `term_dictionary` 검색 결과, 기존 `TermDict` 유지) |
| `difficulty_score` | `float` | 0~100 문서 난이도 |

> ⚠️ **시그니처·필드명 바꾸면 1번에 먼저 공지.** 계약이 깨지면 폐루프가 죽습니다.
> `_meta` 같은 계약 밖 키는 chunk에 싣지 말아주세요(FEEDBACK M2).

---

## 3. Claude → Gemini 무료 전환 (비용0 원칙 유지)

- `restructurer.py`의 **anthropic 호출을 Gemini(Google AI Studio 무료)로 교체**.
- **키는 제가 드립니다** → `GEMINI_API_KEY` (`.env`). SDK: `google-genai`,
  모델 `gemini-2.0-flash` 계열(무료 tier). 정확한 모델ID·분당/일당 한도는 aistudio.google.com에서 확인.
- **폴백 필수**: 키 없음 / 네트워크 실패 / rate limit → **원문 passthrough로 강등**(데모 절대 안 끊기게).
- 🟢 **안심 포인트**: `simplified_text`(재구성문)는 **점수 계산에 안 들어갑니다**(literacy_score는 quiz·focus·difficulty 기반). LLM이 매번 다른 문장을 내도 **점수 재현성은 유지**되니, 재구성엔 Gemini를 자유롭게 써도 됩니다.

---

## 4. 같이 잡아야 할 알려진 블로커 (상세: `FEEDBACK_TO_ROLE2_FROM_ROLE1.md`)

- **H1** RAG 임베딩이 요청·청크마다 전체 용어집 재인코딩 → **1회 캐시** (안 하면 요청당 수십 초)
- **H2** faithfulness 항상 1.0(죽은 코드) → 상수임을 명시하거나 실계산
- **H3** 재구성 라우팅 `term_count` 분기 죽음(용어주입 순서 버그) → 용어주입을 재구성 앞으로
- **M1** CORS `allow_credentials=False`로 3번과 통일
- **M2** `_meta` 계약 누출 제거

---

## 5. 일정

- **7/10 기능 프리즈.** 늦어도 **7/8까지** 붙여주시면 1번이 브릿지→real 교체 후 통합 회귀를 돌립니다.
- 7/8까지 어려우면 임시 브릿지로 데모는 방어되니, 우선순위/ETA만 공유해주세요.
- 기획서 문구(Claude→Gemini) 정정은 **1번이 처리**하겠습니다.

막히면 바로 핑 주세요. 계약 관련 문의는 1번에게. 🙏
