# [1번→3번] O/X 퀴즈 + 이해도 측정 흐름 — 구현 스펙 (v2)

작성: 1번(오케스트레이션) · 대상: 3번(인지케어 백엔드)
문서 목적: **3번이 이 문서만 보고 코드를 만들 수 있도록** 계약·함수 시그니처·알고리즘·폴백을 전부 명시.
소유자 표기: **[3번]** = 3번이 구현 / **[1번·확장]** = 우리가 구현(3번은 계약만 알면 됨) / **[2번]** / **[4번]**

---

## 0. 한 줄 요약

> **2번이 문단별 1문장 요약을 만들고 → 3번이 그 요약으로 O/X 퀴즈를 만든다.**
> **O/X 퀴즈는 딱 하나의 메커니즘**이고, **두 조건 중 하나**로 뜬다:
> **(A) 집중도 하락** 또는 **(B) 본문을 ~90% 읽었는데 아직 퀴즈가 안 나옴(측정 보장).**
> 사용자가 답한 **모든 O/X의 정답률 = 이해도(comprehension)**. → 집중 잘하는 사람도 이해도가 실측된다.
> 웹 인앱 / 확장(웹) / 확장(PDF) **어디서든 동일하게** 뜬다.

기존 "쉬운 문장 재구성(restructuring)"은 폐기. 2번 모델은 대신 **요약**에 쓴다.

---

## 1. 배경 (왜 이 설계인가)

### 1-1. 퀴즈가 안 뜨던 이유
- 오케스트레이터가 `intervention["quiz_data"]`를 **채우는 코드가 없었고**, `frontend_contract.to_intervention_command`도 **`payload.quiz`를 안 실었다**. 확장 `session_client.js`의 `render()`는 `case "quiz"`에서 **토스트만** 띄웠다.

### 1-2. 이해도 측정 문제 (핵심)
- 지금 `score.py`: `comprehension_score = quiz_correct_rate × 100`, 그리고 퀴즈 없으면 `quiz_correct_rate`가 **상수 0.7**을 반환한다.
- 즉 **집중을 너무 잘해서 (개입) 퀴즈가 안 뜨면 이해도가 실측이 아니라 상수 70에 박제**된다. 50% 가중치의 절반이 상수 → 점수 의미가 약해진다.
- 해결: **개입 퀴즈에만 의존하지 말고, 본문을 거의 다 읽은 시점에 "측정 보장" 트리거로 같은 퀴즈를 한 번 더 띄운다.** (별도 퀴즈가 아니라 같은 O/X, 트리거만 추가)

### 1-3. "확장에서 글의 끝을 어떻게 아나?" → 본문 기준 진행률
- 지금 진행률은 `scrollY / 전체페이지높이`(페이지 기준)라 부정확하다(본문 + 댓글 + 광고 + 푸터가 섞임).
- **확장은 이미 본문 문단을 추출**하므로, **본문 문단이 화면에 들어왔는지**로 진행률을 재면 "본문 90% 읽음 / 본문 끝"을 정확히 알 수 있다. (§4에서 스펙)

---

## 2. 전체 흐름

```
[세션 시작]  content[]  ─▶  2번 content_reducer
                              └─ 문단별 1문장 요약 summary  ─▶  chunk.summary
                              [3번] 각 chunk.summary로 O/X 프리젠 ─▶ state["quizzes"]={chunkId: quizData}

[읽는 중]  scroll/blur/pause/position  ─▶  POST /api/session/{id}/events
   [1번·확장] position = "본문 기준" 진행률(0~1)  ← §4
   [3번] focus_score 계산
   [3번] pick_quiz(state): 아래 두 조건 중 하나면 퀴즈 반환, 아니면 None
          (A) focus_score < 30(hard)            ← 재집중 + 측정
          (B) position >= 0.9  AND  퀴즈 아직 부족 ← 측정 보장
          (+ 쿨다운 / 세션당 최대치 / 재출제 방지)
                              │ quizData 반환
   [1번] intervention["quiz_data"] = quizData → to_intervention_command → payload.quiz
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   [웹 인앱 4번]     [확장 웹 1번]      [확장 PDF 1번]
   QuizCard(O/X)    overlay.quiz(O/X)  동일 overlay.quiz
        └───────────────┼────────────────┘
                        ▼  사용자 O/X 선택
        POST /api/session/{id}/quiz/submit  ─▶ [3번] 채점
        └─ state["quiz_answers"].append({quizId, correct, ...})
        └─ 응답 {correct, explanation, focusRecovered, xpEarned}

[세션 종료/결과]  [1번] score.py: comprehension = 답한 모든 O/X 정답률(실측)  ← §6
```

**재사용 포인트:** 확장은 웹·PDF가 `shared/overlay.js`+`shared/session_client.js`를 공용으로 쓴다. → `overlay.quiz()`를 **한 번 만들면 웹·PDF 둘 다** 뜬다.

---

## 3. 역할 분담

| 항목 | 담당 | 산출물 |
|---|---|---|
| 문단 1문장 요약 | **[2번]** | `chunk.summary` (restructured_text 폐기) |
| O/X 생성(요약→진술문) | **[3번] ⭐** | `generate_ox_quiz()` |
| 세션 시작 프리젠·캐시 | **[3번] ⭐** | `state["quizzes"]` |
| 트리거+선택(A/B) | **[3번] ⭐** | `pick_quiz(state)` |
| 채점 + 답변 기록 | **[3번] ⭐** | `POST /quiz/submit`, `state["quiz_answers"]` |
| 개입 주입·계약 노출 | **[1번]** | `intervention["quiz_data"]`, `payload.quiz` |
| 본문 기준 진행률(position) | **[1번·확장]** | `getProgress()` 개편(§4) |
| 확장·PDF 렌더 | **[1번]** | `overlay.quiz()` |
| 이해도 점수 반영 | **[1번]** | `score.py` 상수 0.7 제거(§6) |
| 웹 렌더 | **[4번]** | `QuizCard` O/X 모드 |

⭐ = 3번이 이번에 만들 것.

---

## 4. [1번·확장] 본문 기준 진행률 — position 스펙 (3번은 계약만 알면 됨)

> **3번이 알아야 할 계약:** `/events`로 들어오는 이벤트의 `position`(0~1)은 **"본문 기준 읽은 비율"**이다. `position=1.0` = 본문 끝. `pick_quiz`의 (B) 조건은 이 값을 쓴다. (아래는 확장이 어떻게 만드는지 — 참고용)

**현재(폐기):** `getProgress() = scrollY / (scrollHeight - clientHeight)` (페이지 전체 기준 → 부정확)

**개편(확장 content_script / pdf viewer):**
1. 세션 시작 시 content 추출에 쓴 **본문 문단 DOM 노드 배열 `articleEls[]`를 보관**(인덱스 = content[]/chunk 인덱스와 정렬).
2. **IntersectionObserver로 각 문단의 뷰포트 진입을 관찰.** 문단이 화면에 **누적 체류(dwell) ≥ `max(800ms, 글자수 × 30ms)`** 이면 그 문단을 `readSet`에 추가("스쳐 지나감"은 제외 → 빠른 스크롤 위조 방지).
3. `getProgress()` = `readSet.size / articleEls.length` (본문 기준 0~1). `position = 1.0` = 마지막 문단까지 읽음 = **본문 끝**.
4. 이벤트에 `position`과 함께 **`readChunkIndex`(현재 읽고 있는 문단 인덱스)** 를 실어 보낸다 → 3번이 "지금 어느 문단?"을 안다.
5. **폴백**(문단 노드 확보 실패 사이트): 본문 첫/마지막 추출 요소의 `offsetTop`으로 본문 bounding box를 잡아 `progress = clamp((뷰포트하단_문서좌표 − articleTop) / (articleBottom − articleTop), 0, 1)`. 여전히 본문 기준.
6. **PDF 뷰어**: 이미 `page/total`로 깨끗함 → 그대로 사용(마지막 페이지 = 본문 끝). 원하면 페이지별 dwell 게이트 추가.

---

## 5. [3번] 구현 상세

### 5-1. O/X 퀴즈 생성 `generate_ox_quiz(summary: str, paragraph: str) -> dict`

반환(quiz_data):
```jsonc
{
  "quizId": "",            // 호출부에서 f"quiz_{session_id}_{chunk_id}" 로 채움
  "type": "ox",
  "statement": "이 문단은 X-선의 파장이 가시광선보다 길다고 설명한다.",
  "answer": false,          // true = O(맞다), false = X(틀리다)  ← 서버 보관, 프론트로 안 나감
  "explanation": "본문은 X-선 파장이 가시광선보다 '짧다'고 설명합니다.",
  "sourceChunkId": ""       // 호출부에서 채움
}
```

LLM 프롬프트(권장):
```
[system] 너는 독해 확인용 O/X 퀴즈 출제자다. 원문으로 참·거짓 판별이 가능한 진술문만 만든다.
[user]
문단 요약: "{summary}"
원문 문단: "{paragraph}"
위 내용에 대한 O/X(참/거짓) 진술문 1개를 만들어라.
- answer 는 true/false 를 균등하게 섞어라.
- false일 때는 핵심 사실 하나만 그럴듯하게 왜곡한다(반대말·수치·인과 뒤집기).
- 주관·추측·본문에 없는 내용 금지.
JSON만 출력: {"statement":"...", "answer": true|false, "explanation":"원문 근거 인용"}
```

**키/쿼터 없을 때 폴백(결정론, 데모가 안 죽게):**
- `hash(chunkId) % 2 == 0` → `statement = summary`, `answer = true`, `explanation="요약과 일치합니다."`
- 홀수 → summary의 핵심 서술어/수치를 반대로 뒤집어(늘린다↔줄인다, 짧다↔길다, 부정어 삽입) `answer = false`, `explanation="원문과 반대되는 서술입니다."`
- 항상 유효한 O/X를 반환(빈 값 금지).

### 5-2. 세션 시작 프리젠 `prebuild_quizzes(state) -> None`
- `POST /api/session/start` 처리 직후 호출. 각 `chunk.summary`(+`original_text`)로 `generate_ox_quiz` → `state["quizzes"][chunk_id] = quiz_data`(quizId·sourceChunkId 채움).
- 비용 우려 시: 상위 N개 문단만 프리젠, 나머지는 필요 시 지연 생성+캐시. (개입 순간 생성은 지연 커서 비권장)

### 5-3. 트리거 + 선택 `pick_quiz(state) -> dict | None`  ← 핵심

**호출 위치:** 1번이 `/events` 처리에서 focus 계산 후 이 함수를 부른다. **반환값(quiz_data)이 있으면** 1번이 `state["intervention"]["quiz_data"]`에 넣는다.

**상수:**
```python
HARD_FOCUS_CUTOFF = 30.0     # determine_intervention과 일치
PROGRESS_FLOOR    = 0.9      # 본문 90% 읽으면 측정 보장
MIN_QUIZZES       = 1        # 세션당 최소 보장(이해도 실측 보장)
MAX_QUIZZES       = 3        # 도배 방지
COOLDOWN_MS       = 25_000   # 마지막 퀴즈 후 재출제 금지 간격
```

**알고리즘:**
```
asked   = state.setdefault("asked_quiz_ids", [])
now_ms  = 최근 이벤트 timestamp_ms (없으면 0)
last_ms = state.get("last_quiz_at_ms", -inf)

# 0) 상한/쿨다운
if len(asked) >= MAX_QUIZZES:            return None
if now_ms - last_ms < COOLDOWN_MS:       return None

focus    = state.get("focus_score", 100)
position = max(e.get("position", 0) for e in reading_events)  # 본문 기준 최대 진행률

# 1) 트리거 판정
trigger = None
if focus < HARD_FOCUS_CUTOFF:                                   trigger = "focus_drop"
elif position >= PROGRESS_FLOOR and len(asked) < MIN_QUIZZES:   trigger = "progress_floor"
if trigger is None:                                             return None

# 2) 어느 문단 퀴즈?
if trigger == "focus_drop":
    idx = readChunkIndex(state)          # 지금 읽던 문단(§4의 readChunkIndex, 없으면 position*len)
else:  # progress_floor: 아직 안 낸 문단 중 대표(가장 어려운/중요한 것) 선택
    idx = pick_unused_chunk_index(state, asked)

chunk_id = chunks[idx]["chunk_id"]
quiz = state["quizzes"].get(chunk_id)
if quiz is None or quiz["quizId"] in asked:  return None   # 재출제 방지

# 3) 기록 후 반환
quiz = dict(quiz); quiz["trigger"] = trigger       # 메타(분석용): focus_drop | progress_floor
asked.append(quiz["quizId"])
state["last_quiz_at_ms"] = now_ms
return quiz
```
> **핵심:** 퀴즈는 하나의 메커니즘이고 트리거만 두 개다. (A) 집중 하락은 재집중+측정, (B) 본문 ~90%는 집중 잘한 사람 **측정 보장**. `trigger` 메타만 다르고 UI·채점은 동일.

### 5-4. 채점 엔드포인트 `POST /api/session/{session_id}/quiz/submit`
```jsonc
// 요청 (프론트 apps/web/src/lib/api.ts submitQuizAnswer 계약)
{ "quizId": "quiz_...", "selectedOption": "O" }        // "O" | "X"
// 응답
{ "correct": true, "explanation": "본문 근거: ...", "focusRecovered": 15, "xpEarned": 10 }
```
처리:
1. `state["quizzes"]`에서 quizId로 `answer` 조회. `correct = (selectedOption == "O") == answer`.
2. **답변 기록(이해도 산출용):** `state.setdefault("quiz_answers", []).append({"quizId", "sourceChunkId", "correct": bool, "trigger": quiz.get("trigger")})`.
3. 정답이면 `focus_score`에 보정(+15 등) 반영해 개입 루프 회복 + XP 리워드 반영.
4. `explanation`은 항상 반환(정답이든 오답이든 학습 피드백).

---

## 6. [1번] 이해도 점수 반영 — score.py (3번은 데이터 형태만 맞춰주면 됨)

> **3번이 채워야 하는 것:** `state["quiz_answers"] = [{quizId, sourceChunkId, correct: bool, trigger}]`. 1번은 이걸로 이해도를 실측한다.

**변경(1번):**
```python
answers = state.get("quiz_answers", [])
if answers:
    comprehension_rate = sum(a["correct"] for a in answers) / len(answers)   # 실측
    measured = True
else:
    comprehension_rate = behavioral_proxy(state)   # 폴백(완독률·재독·용어hover 등), 낮은 confidence
    measured = False
comprehension_score = comprehension_rate * 100
# 상수 0.7 박제 제거. quiz_correct_rate(default=0.7) 더 이상 사용 안 함.
```
- `score_breakdown`에 `comprehension_measured: bool`, `quiz_count: int`, `comprehension_confidence` 추가 → 점수가 실측인지 추정인지 드러나게.
- 가중치(0.50/0.35/0.15)·교차검증 감점(최대 20)은 유지.

---

## 7. [모든 표면] 렌더링 요구사항

### 7-1. 웹 인앱 [4번]
- `NudgeController`가 `command.type == "quiz"` & `payload.quiz` 있으면 **`QuizCard`를 O/X 모드**로 렌더.
- `QuizCard`에 **O/X 2버튼 모드** 추가(기존 4지선다와 별개). 선택 시 `api.submitQuizAnswer(sessionId, quizId, "O"|"X")` → 결과 표시.

### 7-2. 확장 웹 + PDF [1번, 공용]
- `shared/session_client.js` `render()` → `case "quiz"`를 **토스트 대신 `overlay.quiz(payload.quiz, onAnswer)`** 로 교체.
- `shared/overlay.js`에 `quiz(quizData, onAnswer)` 추가: 진술문 + [O][X] 버튼 카드. 선택 시 `POST /api/session/{id}/quiz/submit` → 정답/해설 표시.
- **PDF 뷰어(`pdf/viewer.js`)는 같은 shared 모듈 → 자동 지원.**

---

## 8. 트리거·UX 규칙 요약

- **언제:** (A) `focus < 30` **또는** (B) `본문 position ≥ 0.9 & 퀴즈 미달`.
- **쿨다운:** 마지막 퀴즈 후 25초(또는 focus 회복)까지 재출제 금지.
- **상한:** 세션당 최대 3개. **하한:** 최소 1개 보장(측정).
- **재출제 금지:** 같은 문단/quizId 1회.
- **정답 후:** 집중도 회복 + "다시 집중해서 읽어볼까요?" 복귀.

---

## 9. 엣지케이스

- 문단이 너무 짧거나 요약 실패 → 그 문단 퀴즈 스킵.
- LLM 키/쿼터 없음 → §5-1 폴백(결정론 O/X).
- 본문 ~90% 못 읽고 이탈 & focus 하락도 없었음 → 답한 퀴즈 0개 → 이해도는 §6 행동 프록시(추정, `measured=false`). **상수 0.7 금지.**
- PDF 스캔본(텍스트 레이어 없음) → content[]가 비어 세션이 안 열림 → 해당 없음.

---

## 10. 체크리스트

**[3번] 이번에 만들 것**
- [ ] `generate_ox_quiz(summary, paragraph)` + 키 없을 때 결정론 폴백
- [ ] `prebuild_quizzes(state)` → `state["quizzes"]`
- [ ] `pick_quiz(state)` (트리거 A/B + 쿨다운 + 상·하한 + 재출제 방지 + `trigger` 메타)
- [ ] `POST /api/session/{id}/quiz/submit` 채점 + `state["quiz_answers"]` 기록(+focus 회복/XP)
- [ ] 2번에 `chunk.summary`(§0) 요청, 4번에 `payload.quiz`·O/X 렌더(§7-1) 공유

**[1번] (3번 함수/계약 확정되면 붙임)** — 구현 반영 2026-07-12
- [x] `/events`에서 `pick_quiz` 호출 배선(`apply_pick_quiz`) + `to_intervention_command`에 `payload.quiz` 노출(정답·해설 제외)
- [x] `prebuild_quizzes`(세션 시작) + `POST /quiz/submit` 채점(`submit_ox_quiz` → `quiz_answers` 기록·집중 회복·XP), 두 라우터(`/api/reading-sessions`, `/api/session`) 모두
- [x] 확장 `overlay.quiz()`(O/X 카드) + `session_client.render()` `case "quiz"` 교체(토스트→카드+채점 POST)
- [x] `score.py` 상수 0.7 제거, `quiz_answers` 기반 실측 + `measured/confidence`(§6)
- [x] 확장 `getProgress()` 본문 기준 개편(§4) — `shared/reading_progress.js`(IntersectionObserver + dwell 게이팅). `position`이 본문 문단 읽은 비율(0~1)이 되어 (B) 측정 보장 트리거가 정밀 동작. 이벤트에 `readChunkIndex`(현재 읽는 문단)도 동봉 → `_normalize_events`가 통과. PDF는 page/total로 이미 정확해 유지.
- 3번 원본(`generate_ox_quiz`, `select_quiz_for_state`)은 `app/agents/real/quiz_service.py`로 vendored 이식해 사용. 요약 입력은 2번 `chunk.summary` 산출 전까지 `restructured_text`→`original_text` 폴백.

**[2번]** `restructured_text` 폐기 → `summary` 산출
**[4번]** `QuizCard` O/X 모드 + "쉬운 문장" 토글 제거

---

**3번은 §5(생성·트리거·채점)와 §6의 `quiz_answers` 계약, §4의 `position`(본문 기준) 전제만 지키면 이 문서만으로 구현 가능해.**
`generate_ox_quiz` / `pick_quiz`의 시그니처와 `quiz_data`·`quiz_answers` 필드만 확정해서 알려주면, 1번 쪽 배선(개입 주입·payload 노출·확장 overlay·진행률·score.py)은 내가 바로 붙일게. 🙌

---

## 11. Canonical O/X 계약 (2026-07-12 정렬 — 1번·3번·4번 단일 기준)

두 OX 구현(1번 오케스트레이터 · 3번 Cognitive Care 백엔드)과 프론트(4번 QuizCard)를 하나로
맞춘 최종 계약. **이후 이 절이 기준이다.**

### 11-1. 퀴즈 객체 shape (생성 결과)
`generate_ox_quiz(summary, paragraph, chunk_id, session_id)` 반환:
```jsonc
{
  "quizId": "quiz_{session}_{chunk}",
  "type": "ox",
  "question": "이 문단은 …라고 설명한다.",  // 프론트 QuizCard가 렌더(= statement)
  "statement": "…",                        // 확장 overlay.quiz 호환(동일 값)
  "options": ["O", "X"],                   // length===2 → QuizCard가 O/X 2버튼 모드
  "answer": true,                           // 서버 전용(프론트로 절대 안 나감)
  "explanation": "…",                       // 서버 전용(채점 응답에서만 반환)
  "sourceChunkId": "{chunk}"
}
```
- **생성**: 4지선다(`generate_quiz`)에 O/X 버튼 붙이던 방식 폐기. 2번 `chunk.summary`로 참·거짓
  진술문을 만든다(요약 폴백: `summary`→`restructured_text`→`original_text`).
- **payload 노출**: `to_intervention_command`의 `_public_quiz`가 `answer`·`explanation`을 제거하고
  `question`/`statement`/`options`만 내보낸다. → 정답 위조 불가(서버 채점).

### 11-2. 채점(제출) 계약
```jsonc
// 요청  POST /api/session/{id}/quiz/submit
{ "quizId": "quiz_…", "selectedOption": "O" }     // "O" | "X"
// 응답
{ "correct": true, "explanation": "…", "focusRecovered": 15, "xpEarned": 10 }
```
- **서버 채점**: 캐시된 `answer`와 `selectedOption`("O"=true) 비교. 클라이언트가 정답을
  보내지 않는다. (3번 구버전의 `correctOption`/`selectedIndex` 클라이언트 채점·중복 라우트는 폐기.)
- **이해도 반영**: role-1은 `quiz_answers`(문항별) 실측, 3번은 Redis `quiz_result`(집계) 누적 →
  둘 다 `score.py`가 소비(집계는 fallback 경로). `measured=True`.

### 11-3. 채택 근거(둘 중 나은 것)
| 항목 | 채택 | 폐기 |
|---|---|---|
| 생성 | 순수 O/X 진술문(`generate_ox_quiz`+summary) | 4지선다 질문에 O/X 버튼(의미 불일치) |
| 채점 | 서버 채점(정답 미노출) | 클라이언트가 정답 전송 |
| shape | `question`+`options:["O","X"]`(프론트 호환)+`statement`(확장) | `statement`만 / `question`만 |
| 트리거 | role-1 `pick_quiz`(A 집중하락/B 측정보장·쿨다운·상하한) | 단순 position 선택만 |

### 11-4. [4번] 프론트 유의
- `QuizCard`는 `options.length===2`면 이미 O/X 모드로 렌더 → shape 그대로 동작.
- **채점은 `submitQuizAnswer` 응답의 `correct`로 하는 게 정답**(현재 client-side `correctOption`
  비교는 서버가 정답을 안 주므로 항상 index0을 정답 처리 → 오작동). 서버 응답 기반으로 전환 권장.
