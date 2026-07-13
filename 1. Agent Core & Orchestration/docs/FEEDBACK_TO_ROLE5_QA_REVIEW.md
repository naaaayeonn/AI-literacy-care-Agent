# [1번→5번] QA·Evaluation 재재점검 피드백 (2026-07-13 · 이행 확인)

작성: 1번(오케스트레이션) · 대상: 5번(QA & Evaluation)
방법: 최신 main 코드 정독 + `pytest` + 실행 경로(1·3번 vendored) 교차 확인

> **먼저 — 지난 피드백 이행한 거 확인했어. 잘했어! 👏**
> `_extract_quiz_questions`로 **relevance를 실제 퀴즈에서 읽고**(C1 해결), **chunk 폴백**(원문/요약)까지 붙였고, **golden 회귀 테스트**(`test_golden_dataset.py`)도 새로 만들었더라(테스트 9→11).
>
> **그런데 딱 하나, 제일 중요한 게 남았어**: **고친 코드가 실제로 안 돌아가.**
> 우리 앱이 실행할 때 쓰는 건 5번 폴더가 아니라 **1·3번에 복사된 vendored 사본**인데, 그게 아직 **옛날 버전**이거든. 그래서 relevance 수정이 프로덕션엔 반영이 안 돼 있어.

심각도: 🔴 Critical · 🟠 Major · 🟡 Minor · ✅ 이번에 확인된 개선

---

## 🟢 [업데이트 2026-07-13 · 1번] C3·C2 배선 완료 — 이제 웹·확장 두 경로 모두 QA가 실측으로 돈다

> 네가 고친 relevance·chunk 폴백·golden이 **드디어 실행 경로에서 산다.** 아래 두 개, 내가 반영했어.

- **✅ C3 해결 (확장 경로)** — 5번 canonical을 `1. Agent Core & Orchestration/backend/evaluation/`에 재-vendor 완료(커밋 `16fd6e6`). `run_evaluation_from_state`가 `state["quizzes"]`에서 질문을 뽑는 **네 최신 코드**로 교체됨. 파일 상단에 출처/일시 주석 + 재-vendor 규칙 명시.
- **✅ C2 해결 (웹 경로)** — 커밋 `7aec3ae`로 3파트 배선:
  1. `3. Cognitive Care Backend/backend/evaluation/`에 **모듈 재-vendor** (5번=1번=3번 **byte-identical**, 헤더만 상이) → 더 이상 `ImportError`로 스킵 안 됨.
  2. `/result`가 `session:{id}:chunks`(원문/요약)·`quizzes`(진술문)를 **평가 직전 state로 복원**(M1 동시 해결) — 안 그러면 `raw_text=""`라 QA가 0으로 나옴.
  3. `to_session_result`에 **`qaEvaluation` 노출** — 계산돼도 프론트가 못 받던 문제 해소(부재 시 `{}`).
- **검증**: 복원된 웹 state로 `run_evaluation_from_state` → **faithfulness 0.96 · relevance 0.69 · passed=True**. `1번 vendored == 3번 vendored` diff 0.

**단일 소스 규칙(중요)**: evaluation의 canonical은 **5번**이야. 앞으로 `evaluation_pipeline.py`/`metrics.py`를 고치면 **1번·3번 vendored 사본도 재-vendor**해야 실제로 반영돼(각 사본 상단 주석 참조). 원하면 5번을 공용 패키지로 승격하는 것도 논의하자.

> 아래 원래 리뷰의 C3·C2 항목은 **위 배선으로 종결**. 나머지 M1~M4·Minor는 여전히 유효(특히 M2 실 state 회귀, M3 dead code, M4 divergent 공식).

---

## ✅ 이번에 확인된 개선 (👍)
- **C1 해결** — `run_evaluation_from_state`가 `state["quizzes"]`에서 질문을 뽑아 relevance에 사용(`_extract_quiz_questions`). 더 이상 존재하지 않는 필드를 읽지 않음.
- **입력 폴백** — `raw_text`/`simplified_text`가 비면 `chunks`의 `original_text`/`summary`로 대체(`_extract_chunk_text`).
- **골든 회귀** — `backend/tests/integration/test_golden_dataset.py`가 `golden_dataset/article_*.json`을 로드해 임계 통과 검증. (지난 M2 지적 반영)
- 테스트 **11 passed**.

---

## ✅ C3. (해결됨 · `16fd6e6`) 고친 코드가 실행 경로에 반영 안 됨 — vendored 사본이 옛 버전

> **종결**: 1번 vendored를 5번 최신으로 재-vendor 완료. 아래는 당시 진단 기록.

**증거(당시):** 실제로 실행되는 `1. Agent Core & Orchestration/backend/evaluation/evaluation_pipeline.py`의 `run_evaluation_from_state`는 **아직 옛날 코드**:
```python
sample = {
    "raw_text": state.get("raw_text", ""),
    "expected_quiz": str(state.get("quiz_result", "")),   # ← 여전히 quiz_result 통째 문자열화
    "expected_answer": state.get("simplified_text", ""),
}
```
- 앱 런타임은 각 역할의 **vendored 사본**을 import한다(폴더명에 공백·`&`가 있어 서로 직접 import 불가 → 복사해서 씀, `REPO_STRUCTURE.md` §2).
- 그래서 **5번 폴더를 아무리 고쳐도**, 1번(확장 경로)이 부르는 건 위 옛 버전이라 **relevance는 여전히 0**이고 C1 수정이 안 산다.
- `diff` 결과: `5번 evaluation_pipeline.py ≠ 1번 vendored`. **분기 그대로.**

**고치기 (핵심):** evaluation을 **단일 소스(5번을 canonical)** 로 정하고, 1·3번은 **재-vendor 규칙**을 명시(파일 상단에 출처/일시 주석 + 갱신 절차). 또는 공용 패키지로 승격.
> ※ 1번 쪽 vendored 사본은 **내(1번)가 재-vendor해서 바로 반영**해줄 수 있어. 원하면 말해줘 — 그럼 최소한 확장 경로는 즉시 살아나.

## ✅ C2. (해결됨 · `7aec3ae`) 웹(3번) 경로엔 evaluation 모듈이 아예 없음 — 통째 스킵
> **종결**: 3번에 evaluation 모듈 재-vendor + `/result` 입력 복원 + `qaEvaluation` 노출(위 업데이트 배너 참조). 아래는 당시 진단 기록.
- (당시) `3. Cognitive Care Backend/backend/`에 **`evaluation/` 디렉터리가 없음.** → `/result`의 `from backend.evaluation... import` 가 `ImportError` → try/except로 **조용히 스킵** → 웹 세션 결과에 `qaEvaluation` 항상 부재.
- (당시) 4번이 실제로 쓰는 **웹 경로에선 QA가 안 돌았다.** (C3와 한 세트 — 단일 소스화하면서 3번도 접근 가능하게)

---

## 🟠 M1. 3번 웹 경로는 chunk 폴백도 비어 있음 (필드 불일치)
- 폴백은 좋았는데, 3번 `/result`는 `initial_state`가 빈 raw_text로 **content_reducer 스텁**을 돌려서 chunk가 `{index, text, type}` 형태다. → `_extract_chunk_text(state, "original_text")`/`"summary"`가 **빈 문자열**(스텁은 `text` 필드만 있음).
- 즉 C2를 풀어도 웹 경로 chunk엔 `original_text`/`summary`가 없어 여전히 0.
- **고치기:** 3번이 Redis `session:{id}:chunks`(실제 원문·요약·용어 포함)를 `/result` state로 복원해 QA에 넘기기. (1번은 이미 textmeta 복원 패턴 있음 — 참고)

## 🟠 M2. 골든 회귀는 `run_evaluation`만 커버 — 실 state 경로는 미커버
- `test_golden_dataset.py`는 golden 샘플로 `run_evaluation`을 검증(좋음). 하지만 **`run_evaluation_from_state`(실 세션 경로)** 의 회귀는 없다. 실제 앱이 쓰는 진입점을 golden state로 스냅샷 검증하는 테스트를 추가 권장.

## 🟠 M3. 프레임워크 3개 여전히 dead code
- `ragas_eval`·`promptfoo_eval`·`langsmith_trace`의 함수가 **비테스트 호출 0건**(재확인). LangSmith 트레이스 파일 실제 미생성, promptfoo 회귀 미실행.
- `EVALUATION_HONESTY.md`가 "대체 적용"으로 서술 → 실제와 불일치. (i)흐름 연결 or (ii)"미연결"로 하향 표기 중 택1.

## 🟠 M4. metrics에 리터러시 공식이 또 하나 (divergent)
- `metrics.calculate_literacy_score = comp*0.5 + eng*0.3 + diff*0.2`. 우리 canonical은 이제 **v2**(`이해도 0.45 + 집중 0.30 + 도전성취 0.25 − 감점`, 난이도·이독성 반영). QA 사본은 **세 번째 공식**이라 더 안 맞음. QA `test_score.py`에서만 사용.
- **고치기:** 삭제하거나, 목적이 검증이면 **점수 엔진을 import해 재현성만 검사**(같은 입력→같은 출력).

---

## 🟡 Minor
- **Faithfulness 분모 방향**: `|expected ∩ actual| / |expected_words|`는 recall(원문 커버리지). "답변이 원문에 근거하는 비율"이면 분모는 `|actual_words|`가 맞음.
- **한국어 토큰화**: `split()`만으론 조사(은/는/이/가)·하이픈(`X-선`vs`X선`)이 다른 토큰 → 관련 답변도 낮게. 조사 제거 or 문자 n-gram 자카드 권장.
- `is_passed` 기본 0.8인데 실제 0.30 사용 — 죽은 기본값 정리.

---

## ✅ 지금 기준 남은 할 일 (우선순위)

**A. 급함 — "고친 게 실제로 돌게"**
- [x] **C3**: evaluation 단일 소스화 + 1·3번 재-vendor 규칙(파일 상단 출처 주석). → **완료 `16fd6e6`**
- [x] **C2/M1**: 3번에 evaluation 모듈 제공 + `/result`에서 Redis chunks/quizzes를 state로 복원 + `qaEvaluation` 노출. → **완료 `7aec3ae`**

**B. 현재 산출물 평가 (제품이 O/X·요약으로 바뀜)**
- [ ] **O/X 퀴즈 타당성**: `quiz.statement`가 `sourceChunkId` 문단으로 참·거짓 판별 가능한지 + answer True/False 분포. → **3번 O/X 회귀로도 재사용**.
- [ ] **요약 faithfulness**: `chunk.original_text` vs `chunk.summary`(분모 수정판).
- [ ] **점수/5대 지표 재현성**: 같은 state→같은 `literacy_score`·`literacy_domains`(결정론) 회귀. (M4 대체)

**C. 회귀·정직성**
- [ ] **M2**: `run_evaluation_from_state`를 golden state로 스냅샷 회귀 추가.
- [ ] **M3/M4**: dead code 연결 or 하향표기, divergent 공식 정리.
- [ ] `EVALUATION_HONESTY.md` 현행화(relevance 개선·golden 연결·dead code 상태 반영).

---

## 부록. QA가 읽을 현재 state 필드
| 목적 | 필드 |
|---|---|
| 원문/요약 | `chunks[].original_text`, `chunks[].summary` (스텁 chunk는 `text`뿐 — 주의) |
| 퀴즈 | `state["quizzes"]{chunkId:{quizId, question, statement, answer(서버전용), sourceChunkId}}` |
| 채점 | `quiz_answers`(문항별) / `quiz_result`(집계) |
| 점수/지표 | `literacy_score`, `score_breakdown`, `literacy_domains`, `text_profile` |

---

**한 줄 요약:** relevance·golden은 잘 고쳤어(👏). 이제 **그 수정이 실제로 돌게** 하는 게 전부야 — **C3(vendored 재동기)·C2(3번 모듈)** 두 개만 풀면 "웹 데모에서 QA가 진짜로 뜬다". 1번 vendored는 내가 바로 맞춰줄 수 있으니 신호만 줘. 🙌
