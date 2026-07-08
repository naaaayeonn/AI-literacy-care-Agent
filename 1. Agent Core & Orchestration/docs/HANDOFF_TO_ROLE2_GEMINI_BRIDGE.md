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

**채워야 할 필드 (snake_case · ReadingSessionState 계약) — 2번 `contracts.py` 형태 그대로:**

| 필드 | 타입 | 내용 |
|---|---|---|
| `chunks` | `list[ChunkDict]` | `{chunk_id, original_text, restructured_text?, difficulty, terms?, char_start, char_end}` |
| `simplified_text` | `str` | 전체 재구성 텍스트(프론트 전체보기용) |
| `terms` | `list[TermDict]` | `{term, definition, source, faithfulness_score?, chunk_id}` (사전 검색) |
| `difficulty_score` | `float` | 0~100 (= 100 − readability) |

> ⚠️ **시그니처·필드명 바꾸면 1번에 먼저 공지.** 계약이 깨지면 폐루프가 죽습니다.
> `_meta` 같은 계약 밖 키는 chunk에 싣지 말아주세요(FEEDBACK M2).
>
> 📌 **1번이 이미 해둔 것**: (a) `term_dictionary.json`(106개)을 1번 레포에 이식해 오프라인 검색으로 붙임,
> (b) `restructurer`를 **Gemini 무료(google-generativeai)**로 호출하는 임시 어댑터 작성 —
> `gemini-flash-latest`부터 시도하고 **모델별 quota 소진 시 다음 모델로 폴백**(2.5-flash-lite→2.5-flash),
> 전부 실패하면 원문 passthrough. 2번은 이 방식을 참고해 자기 `restructurer.py`에 반영하면 됩니다.
> (무료 tier는 모델마다 PerDay quota가 따로 소진되니 **폴백 체인 권장**.)

---

## 3. Claude → Gemini 무료 전환 (비용0 원칙 유지)

- `restructurer.py`의 **anthropic 호출을 Gemini(Google AI Studio 무료)로 교체**.
- **키는 제가 드립니다** → `GEMINI_API_KEY` (`.env`). SDK는 `google-generativeai`(설치돼 있음) 사용.
- **모델은 폴백 체인**: 이 키는 `gemini-2.0-flash`·`gemini-2.5-flash`가 **PerDay quota 소진** 상태 →
  `gemini-flash-latest`부터 시도하고 429 시 다음 모델로 폴백(1번 브릿지 `_restructure` 참고).
  무료 tier는 모델마다 quota가 따로라 **폴백 체인 필수**. (데모 당일 여유 있는 키 하나 더 있으면 안전.)
- **폴백 필수**: 키 없음 / 네트워크 실패 / 전 모델 quota 소진 → **원문 passthrough로 강등**(데모 절대 안 끊기게).
- 🟢 **안심 포인트**: `simplified_text`(재구성문)는 **점수 계산에 안 들어갑니다**(literacy_score는 quiz·focus·difficulty 기반). LLM이 매번 다른 문장을 내도 **점수 재현성은 유지**되니, 재구성엔 Gemini를 자유롭게 써도 됩니다.

---

## 4. 같이 잡아야 할 알려진 블로커 (상세: `FEEDBACK_TO_ROLE2_FROM_ROLE1.md`)

- **H1** RAG 임베딩이 요청·청크마다 전체 용어집 재인코딩 → **1회 캐시** (안 하면 요청당 수십 초)
- **H2** faithfulness 항상 1.0(죽은 코드) → 상수임을 명시하거나 실계산
- **H3** 재구성 라우팅 `term_count` 분기 죽음(용어주입 순서 버그) → 용어주입을 재구성 앞으로
- **M1** CORS `allow_credentials=False`로 3번과 통일
- **M2** `_meta` 계약 누출 제거

---

## 5. 🔑 용어 커버리지 확대 (2번 TODO — 현재 106개는 부족)

> 배경: 임시 브릿지는 `term_dictionary.json` **106개(대부분 IT 도메인)**만 검색해서, 일반 글에선
> 툴팁이 거의 안 뜹니다. "환각 없는 용어풀이"가 헤드라인인데 **커버리지가 좁으면 기능이 약해 보임**.
> 이건 RAG 영역이라 **2번 몫**입니다(1번 브릿지는 데모용 최소 검색만 유지, 확대는 안 함).

선택지(환각0 유지 vs 커버리지):

| 방법 | 커버리지 | 환각 | 비용/의존 |
|---|---|---|---|
| **A. 국립국어원 오픈 API** (표준국어대사전/우리말샘/한국어기초사전) | 광범위(수만~100만) | 0(진짜 사전) | 무료·인증키·네트워크 |
| **B. `term_dictionary.json` 확장** (`scripts/expand_dictionary.py`) | 중간(수백~수천) | 0 | 무료·오프라인·큐레이션 |
| **C. 하이브리드** (사전 우선 + 미수록은 Gemini, "AI설명(참고용)" 라벨) | 무제한 | ⚠️ 생성분 명시 | 무료 |

권장:
- **`terms`(미리 하이라이트)**: 사전/확장 기반 유지(큐레이션 품질) — B 또는 A로 확대.
- **hover 단건 lookup**(§E3): **국립국어원 API가 최적** — 사용자가 올린 단어를 그때 조회 → 어떤 단어든
  진짜 뜻. 커버리지 문제 근본 해결. (기획서 인용 출처가 표준국어대사전이라 명분도 정확.)
- 검증됨(무료): 표준국어대사전 API `https://stdict.korean.go.kr/api/search.do`(JSON 지원, 인증키 필요),
  우리말샘 `https://opendict.korean.go.kr/api/search`, 한국어기초사전(krdict, **하루 5만건 무료 명시**).
  ※ 인증키는 신청·승인 절차가 있으니 **일정 여유 두고 미리 발급**. 표준국어대사전은 승인 지연 가능성 →
  발급 쉬운 우리말샘/기초사전도 국립국어원 신뢰출처라 대안 가능.
- ⚠️ API는 "단어→뜻" 조회라 **어떤 단어를 뽑을지(후보 선정)는 별도 문제**(형태소 분석 등). hover엔 완벽하나
  미리 하이라이트엔 후보 추출 로직이 필요.

---

## 6. 일정

- **7/10 기능 프리즈.** 늦어도 **7/8까지** 붙여주시면 1번이 브릿지→real 교체 후 통합 회귀를 돌립니다.
- 7/8까지 어려우면 임시 브릿지로 데모는 방어되니, 우선순위/ETA만 공유해주세요.
- 기획서 문구(Claude→Gemini) 정정은 **1번이 처리**하겠습니다.

막히면 바로 핑 주세요. 계약 관련 문의는 1번에게. 🙏
