# [1번→3번] 퀴즈·Growth 백엔드 비판적 코드 리뷰 (2026-07-13)

작성: 1번(오케스트레이션) · 대상: 3번(Cognitive Care Backend)
검토 범위: `3. Cognitive Care Backend/backend/app` 최신 main (`73d9556` 기준)
 — `api/endpoints.py`, `services/quiz_service.py`, `api/frontend_contract.py`, `api/users.py`, `models/models.py`

> **TL;DR — 지금 상태로는 데모에서 티가 납니다.**
> 1. **채점이 틀립니다.** LLM(SnowChat)이 켜지면 화면에 뜬 퀴즈와 채점하는 정답이 **서로 다른 퀴즈**입니다. (C1)
> 2. **정답이 프론트로 그대로 나갑니다.** `answer`·`explanation`을 안 지우고 내려줘서 위조·컨닝 가능. (C2)
> 3. **Growth의 독해시간/XP는 영구 0입니다.** `duration_seconds`·`xp_earned`를 **아무 데서도 DB에 안 씁니다.** "고쳤다"고 한 `/result` 세션 갱신도 실제 코드엔 없습니다. (C3)
> 4. **문해 5대 지표는 가짜 매핑입니다.** literacy/engagement 두 값을 `+5~+15` 오프셋으로 늘려 5개인 척하고, `before`는 항상 50 고정. (M1)

심각도: 🔴 Critical(정확성 깨짐) · 🟠 Major(데이터/UX) · 🟡 Minor(정리)

---

## 🔴 C1. JIT 재생성 퀴즈가 Redis에 저장되지 않아 채점이 어긋남

**위치:** `services/quiz_service.py` `select_quiz_for_state` L80~117(및 중복 L136~171), `api/endpoints.py` `process_events` L186~192, `submit_quiz` L216~226

**무슨 일이 일어나나:**
- `/events`에서 퀴즈를 고를 때(`select_quiz_for_state`) SnowChat이 켜져 있으면 **그 자리에서 LLM로 statement·answer·explanation을 새로 생성**해 `quiz` 딕셔너리를 **덮어씁니다**(L110~114).
- 그런데 이 변경된 `quizzes`를 **Redis(`session:{id}:quizzes`)에 다시 저장하지 않습니다.** `/events`는 `asked_quizzes`만 저장합니다(L192).
- 사용자가 답을 내면 `submit_quiz`는 `session:{id}:quizzes`를 **다시 읽어**(L216) `target_quiz["answer"]`로 채점합니다(L226). → 이건 **start 시점의 결정론 정답**이지 화면에 뜬 JIT 퀴즈의 정답이 아닙니다.

**결과:** 화면엔 "엑스선은 파장이 짧다(정답 O)"가 떴는데, 서버는 다른 문장의 hash 기반 정답으로 채점 → **맞게 눌러도 오답 처리**되고, 돌아오는 해설도 엉뚱한 문장의 것. (LLM이 answer를 `무작위 True/False`로 뽑으라고까지 해서 불일치가 사실상 보장됩니다 — L91.)

> 참고: SnowChat **키가 없으면** JIT가 안 돌아 표시=채점이 우연히 일치하지만, 그땐 대신 저품질 결정론 퀴즈(아래 M5)가 뜹니다. 즉 **켜도 문제, 꺼도 문제.**

**고치는 법(택1):**
- (권장) JIT 결과를 만든 뒤 `state["quizzes"]`를 **Redis에 다시 저장**하고, 같은 quizId는 **한 번만 생성해 캐시**(비결정성 제거). `select`가 매 배치 재생성하지 않도록 `quiz.get("generated")` 플래그로 가드.
- 또는 JIT를 폐기하고 `/start`에서 한 번만 생성해 캐시(결정론). LLM 품질이 필요하면 start에서 LLM 호출.

---

## 🔴 C2. 정답·해설이 프론트로 유출 (`_public_quiz` 미적용)

**위치:** `api/frontend_contract.py` `to_intervention_command` L71~72

```python
elif front_type == "quiz" and "quiz_data" in intervention:
    payload["quizzes"] = intervention["quiz_data"]   # answer·explanation 그대로 실림
```

- `quiz_data`(퀴즈 dict들)를 **필터 없이** payload에 실어 내려줍니다. `answer`(정답 bool)·`explanation`이 클라이언트로 그대로 전송됩니다.
- 이전 canonical 정렬(`43597b6`)에서 1번이 넣었던 `_public_quiz`(answer·explanation 제거)가 **여기선 빠졌습니다.** 서버 채점을 하는 이유(위조 방지)가 무력화됩니다.

**고치는 법:** 내보내기 직전에 각 퀴즈에서 `answer`·`explanation` 제거.
```python
def _public_quiz(q: dict) -> dict:
    return {k: v for k, v in q.items() if k not in ("answer", "explanation")}
payload["quizzes"] = [_public_quiz(q) for q in intervention["quiz_data"]]
```
해설은 지금처럼 `/quiz/submit` 응답으로만 돌려주면 됩니다(이미 그렇게 하고 있음).

---

## 🔴 C3. Growth 독해시간/XP가 영구 0 — 세션 통계가 DB에 안 써짐

**위치:** `models/models.py`(컬럼 존재) vs `api/endpoints.py`(기록 부재), `api/users.py` `get_user_growth` L59~61

- `ReadingSession`엔 `xp_earned`, `duration_seconds` 컬럼이 있고(L21~22), `get_user_growth`는 이걸 `sum`합니다(L59~61).
- 그런데 **`session.duration_seconds`·`session.xp_earned`에 값을 대입하는 코드가 백엔드 전체에 한 줄도 없습니다.** (grep 확인) → 항상 `null` → `sum`=0 → **독해시간 0분, 획득 XP 0.**
- 게다가 소희에게 공유된 수정안(“`/result`에서 세션 통계 UPDATE”)이 **실제 `get_session_result`(L314~394)엔 없습니다.** 이 함수는 이벤트만 DB flush하고 `final_state`를 계산해 반환할 뿐, `session.literacy_score/comprehension/engagement/xp/duration`을 **하나도 세션에 안 씁니다.**
- `finish_session`(L248~312)은 literacy/comprehension/engagement는 쓰지만 **duration·xp는 안 쓰고**, 무엇보다 **클라이언트는 `/finish`를 호출하지 않습니다**(3번 버그리포트 본인 명시). → 그래서 세션 점수도 대부분 null.

**결과:** radar는 `avg = (… or 50)` 폴백으로 전부 ≈50~65에 몰리고, 독해시간·XP는 0. "Growth 실연동"이 사실상 미완.

**고치는 법(클라가 `/result`를 부르므로 `/result`에서 처리):** `final_state` 계산 직후 세션에 영속.
```python
final_state = run_reading_session(initial_state)
session.literacy_score      = final_state.get("literacy_score")
bd = final_state.get("score_breakdown", {})
session.comprehension_score = bd.get("comprehension_score")
session.engagement_score    = bd.get("engagement_score")
session.xp_earned           = int(final_state.get("reward", {}).get("xp", 0))   # 1번 reward에서
ts = [e["timestamp_ms"] for e in state_events if e.get("timestamp_ms") is not None]
session.duration_seconds    = int((max(ts) - min(ts)) / 1000) if len(ts) >= 2 else 0
await db.commit()
return to_session_result(final_state)
```
> `reward.xp`는 1번 파이프라인이 이미 채웁니다(`final_state["reward"]["xp"]`). duration은 이벤트 timestamp 범위로 계산.

---

## 🟠 M1. 문해 5대 지표가 가짜 매핑 (핵심 지적)

**위치:** `api/users.py` `get_user_growth` L80~86

```python
radar_data = [
    {"subject": '어휘력',   "before": 50, "after": min(100, int(avg_lit + 10))},
    {"subject": '독해 속도', "before": 50, "after": min(100, int(avg_eng + 5))},
    {"subject": '정독율',   "before": 50, "after": min(100, int(avg_comp + 15))},
    {"subject": '추론 능력', "before": 50, "after": min(100, int(avg_lit + 5))},
    {"subject": '집중 유지', "before": 50, "after": min(100, int(avg_eng + 10))},
]
```
- 실제로는 **literacy·engagement·comprehension 3개 신호**를 `+5~+15` 임의 오프셋으로 늘려 5개인 척한 것. **어휘력=추론능력=literacy+offset**, **독해속도=집중유지=engagement+offset** — 서로 다른 역량이 아님.
- `before`는 **항상 50 고정**(케어 미적용 통제군 없음) → "성장 스토리"가 통계가 아니라 연출.
- C3 때문에 `avg_*`가 대부분 폴백 50이라 결국 전부 50~65.

**권장: 우리가 실제로 측정하는 신호에서 5대 지표를 정직하게 파생.** (아래 §부록 A 매핑을 그대로 채택 가능)

---

## 🟠 M2. activityData 주간 분포가 가짜

**위치:** `api/users.py` L65~73 — `total // 7, total // 6, … total`

- 일자별 실제 데이터가 아니라 **누적 총량을 나눗셈으로 흩뿌린** 모양만 주간. 요일 순서대로 우상향하는 건 데이터가 아니라 `//7 < //6 < …` 산식 때문.
- 실제로 하려면 `ReadingSession`에 **생성 시각(created_at)** 을 두고 요일/주차별로 `group by` 집계해야 함(현재 모델에 타임스탬프 컬럼 확인 필요).

---

## 🟠 M3. 퀴즈 스팸 — 쿨다운·상한 없음

**위치:** `api/endpoints.py` `process_events` L173~192, `select_quiz_for_state`(최대 3개 반환)

- `focus < 30`이면 **매 이벤트 배치마다** hard→`select_quiz_for_state`가 **한 번에 최대 3개** 퀴즈를 띄웁니다. 집중이 계속 낮으면 배치마다 팝업.
- `current_progress >= 100`이면 `ignore_asked=True`로 **이미 푼 퀴즈까지 무한 재출제**(L185~186). 완독 후 `/events`가 또 오면 또 3개.
- 1번 오케스트레이터의 `pick_quiz`엔 **쿨다운(25s)·세션당 상한(MAX 3)·재출제 금지**가 있습니다. 3번도 최소한 (a) 쿨다운, (b) 세션 상한, (c) 한 번에 1개를 권장. 완독 마무리 퀴즈는 **세션당 1회만** 트리거되게 플래그.

---

## 🟠 M4. 계약 재분기 — `payload.quizzes`(리스트) vs 1번 `payload.quiz`(단수)

- 3번+4번은 `payload.quizzes`(배열, 최대 3) + `setActiveQuizzes`로 갔습니다(`apps/web/.../ReadingPage.tsx` L77, `QuizCard.tsx`, `focusStore.ts`).
- 1번(오케스트레이터)·확장은 canonical `payload.quiz`(**단수**, answer 제거)를 씁니다(`session_client.render()`의 `case "quiz"` → `payload.quiz`).
- 즉 **웹↔3번은 quizzes(복수), 확장↔1번은 quiz(단수)** 로 갈렸습니다. 지금은 백엔드가 둘로 나뉘어(웹=3번, 확장=1번) 각자 돌지만, 하나의 계약으로 못 부릅니다.

**정리 제안(§부록 B):** payload에 **둘 다** 싣거나(`quiz`=배열의 첫 번째, `quizzes`=배열), 팀이 "복수"로 통일하되 **1번/확장도 배열을 수용**하도록 맞추기. 어느 쪽이든 **answer 제거는 공통 필수**(C2).

---

## 🟠 M5. `generate_ox_quiz` 홀수 브랜치가 무의미 진술 + "[요약]" 노출

**위치:** `services/quiz_service.py` L25~28

```python
else:
    statement = "이 문단은 앞의 내용과 완전히 반대됩니다."   # 내용과 무관한 상수
    answer = False
```
- 홀수 chunk는 **본문과 아무 상관없는 고정 문장**(항상 False). LLM이 안 켜지면 문서의 절반이 이 문장 → O/X의 의미가 사라짐.
- 짝수 브랜치는 `summary` 첫 문장을 그대로 쓰는데, 2번의 요약 폴백은 `"[요약] …"` 프리픽스가 붙습니다(2번 `summarize_chunk`). → 화면에 `"[요약] 엑스선은…"`이 그대로 노출.

**고치는 법:** 홀수 브랜치도 summary 기반으로 **핵심 서술어/수치를 반전**(늘린다↔줄인다, 짧다↔길다, 부정어 삽입)해 그럴듯한 False를 생성(편지 원안 §5-1). `[요약]` 프리픽스는 `statement`에 넣기 전 `strip`.

---

## 🟠 M6. 어휘 보드가 실데이터 아님

**위치:** `api/users.py` L96 — `event_type == "dictionary_lookup"`

- 이 이벤트를 **아무도 발신하지 않습니다**(웹·확장 어디에도 `dictionary_lookup` 없음). → 항상 하드코딩 2개(AX/Canary)로 폴백.
- 실데이터로 하려면 프론트/확장이 **용어 클릭(hover/lookup) 이벤트**를 보내야 함 → 4번·확장 협의 필요. 아니면 "이번 주 어휘"는 **본문에서 뽑힌 2번 `terms`** 로 대체(세션에 저장된 terms에서 난이도 상위 N개).

---

## 🟡 Minor (정리)

- `start_session`에서 `redis_client = await get_redis()`가 **두 번**(L47, L105) — 하나로.
- 대부분 핸들러의 `try/finally: pass`는 **죽은 코드**. `finally`에서 `await redis_client.aclose()` 안 하면 실 Redis에서 커넥션 누수(데모 InMemory라 당장은 무해).
- `select_quiz_for_state`의 JIT 프롬프트/파싱 블록이 **두 번 복붙**(L80~117, L136~171) — 헬퍼로 추출.
- `_completion_rate`는 `position(0~1)×100` 가정. 웹 프론트가 position을 **0~1로 보내는지** 확인 필요(0~100로 보내면 `>=100`이 상시 참 → 퀴즈 오발). 확장은 0~1 확정.
- `request_quiz` 이벤트가 `calculate_focus_score`엔 무시되는 타입이라 focus엔 영향 없음(OK). 다만 이벤트 정규화에서 걸러지지 않는지 확인.

---

## ✅ 3번이 더 해야 할 것 (우선순위 Action Items)

- [ ] **[C3]** `/result`에서 `session.duration_seconds`·`xp_earned`·`literacy/comprehension/engagement` 영속 + `commit`. (독해시간/XP 0 해결의 유일 경로)
- [ ] **[C1]** JIT 퀴즈를 Redis에 재저장하거나 start 1회 생성으로 결정론화 → 표시=채점 정합.
- [ ] **[C2]** `to_intervention_command`에서 `answer`·`explanation` 제거(`_public_quiz`).
- [ ] **[M1]** 5대 지표를 실측 신호 파생으로 교체(§부록 A).
- [ ] **[M3]** 퀴즈 쿨다운/세션 상한/완독 1회 트리거.
- [ ] **[M5]** 홀수 O/X를 summary 반전으로 생성 + `[요약]` strip.
- [ ] **[M2/M6]** activity는 실제 세션시각 집계, 어휘 보드는 terms 기반 or lookup 이벤트 도입.
- [ ] **[M4]** payload 계약(quiz vs quizzes) 팀 합의·문서화.
- [ ] **[Minor]** 중복 redis·죽은 finally·복붙 JIT 정리.

---

## 부록 A. 문해 5대 지표 — 실측 파생 매핑(권장)

우리가 실제로 뽑는 신호만으로 정직하게 재정의(1번 `score.py` 산출값 기준). 각 0~100.

| 새 지표 | (구) | 공식 | 근거 신호 |
|---|---|---|---|
| **이해도** | 유지 | `comprehension_score` | O/X 정답률 실측(quiz_answers) |
| **집중 유지** | 유지 | `engagement_score` | focus, 이벤트 기반(blur/pause/스키밍 감점) |
| **정독 충실도** | 정독율 | 본문기준 완독률(§4 dwell 게이트) | reading position 최대값 |
| **읽기 안정성** | 독해 속도 | `100 − 정규화(스키밍+이탈+무동작+과체류 감점)` | `penalty_breakdown` |
| **케어 회복력** | 추론 능력 | 개입 후 집중 회복 성공률(개입 없으면 완독률 대체) | 개입→퀴즈→focus 회복 |

- 5개 전부 우리 메커니즘에 1:1 대응 → 데모에서 "왜 이 점수인지" 근거를 댈 수 있음.
- **before/after**: 통제군이 없으므로 라벨을 **"첫 세션→현재"**(세션 히스토리)로 바꾸는 걸 권장. 고정 50은 지양.
- 1번이 `score.py`에 `compute_literacy_domains(state)→{5값}`을 넣어 세션 result로 노출할 수 있음. 그러면 3번은 세션에 이 5값(JSON 1컬럼)만 저장하고 `/growth`에서 평균만 내면 됨. **원하면 1번이 이 계산 함수 먼저 붙여줄게.**

## 부록 B. 퀴즈 payload 계약(정리안)

```jsonc
// 개입 명령(webSocket/REST) payload — answer·explanation 제거 필수
{ "type": "quiz",
  "payload": {
    "quiz":   { "quizId","type":"ox","question","statement","options":["O","X"],"sourceChunkId" },  // 단수(호환)
    "quizzes":[ …위 객체 배열… ]   // 복수(웹 다중 출제)
} }
// 채점: POST /api/session/{id}/quiz/submit  { quizId, selectedOption:"O"|"X" }
//   → { correct, explanation, focusRecovered, xpEarned }   ← 해설은 여기서만
```

---

문의는 언제든. C3(Growth 0)과 C1(채점)·C2(정답유출)만 먼저 잡으면 데모 신뢰도가 확 올라갑니다. 🙌
