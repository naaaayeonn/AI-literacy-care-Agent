# 4번(프론트엔드 & 시각화 · apps/web) 코드 리뷰 피드백 — from 1번(오케스트레이션)

> 검토일: 2026-07-06 · 대상: `naaaayeonn/AI-literacy-care-Agent` 브랜치 `feature/frontend-setup` → `apps/web/`
> 검토 범위: `lib/{api,ws,useScoreEngine}.ts · stores/{focus,reading,score}Store.ts · types/shared.ts ·
> pages/ReadingPage.tsx · components/nudge/NudgeController.tsx · components/reading/ReadingPane.tsx ·
> (참고) QuizCard/TermTooltip/LiteracyScoreChart/FloatingControlPanel`
>
> 컴포넌트 완성도·디자인 토큰·Zustand 구조·WS 클라이언트/이벤트 방출까지 **UI 레이어는 매우 탄탄**합니다.
> 문제는 대부분 **백엔드(3번) 실제 계약과의 정합**입니다. "M2 실제 백엔드 연동 완료"로 표기돼 있으나,
> 아래 스키마 불일치 때문에 **실연동이 조용히 mock으로 폴백**되고 있습니다. 심각도 순으로 정리했습니다.
>
> ※ 이 리뷰는 **웹앱(데모 폴백)** 대상입니다. 확장 UI(팝업 온보딩·오버레이 퀴즈 모달·단어 툴팁)는
> `extension/` 별도 산출물이라 여기 포함되지 않습니다(그쪽은 4_DELIVERY_PLAN에서 별도 추적).

---

## 🔴 High — 실연동이 실제로 안 됨 (조용한 mock 폴백)

### A1. `startSession` 요청·응답 필드가 3번 백엔드 계약과 불일치 → 항상 mock 세션
- **위치**: `lib/api.ts:141~159`
- **증상**:
  - **요청**: `body: { user_id, document_id }` (snake_case) 를 보냄. 그러나 3번 `schemas.SessionStartRequest`는 **`{ userId, articleId }`(camelCase, 필수)**. → pydantic **422** → `res.ok=false` → **catch도 아닌 채로 mock 폴백**으로 빠짐.
  - **응답**: 성공 시 `sessionId: data.session_id`로 읽음. 그러나 3번 `SessionStartResponse`는 **`sessionId`(camel)**를 반환 → 설령 200이어도 `data.session_id`는 **undefined**.
    ```ts
    // 지금 (api.ts) — 양쪽 다 어긋남
    body: JSON.stringify({ user_id: req.userId, document_id: req.articleId }),  // ← userId/articleId 여야
    ...
    return { sessionId: data.session_id, ... }   // ← data.sessionId 여야
    ```
- **영향**: `POST /api/session/start` 실연동이 **항상 실패 → mock 세션 사용**. 그 결과 wsEndpoint가 `ws://…/ws/reading/mock-session-…`가 되어 **DB에 없는 세션**으로 붙음 → 이후 `GET /result`는 404(또는 3번 H1 크래시). "M2 연동 완료"가 사실상 미작동.
- **수정안**: 요청/응답을 3번 계약(camelCase)에 맞춤.
  ```ts
  body: JSON.stringify({ userId: req.userId, articleId: req.articleId }),
  const data = await res.json();
  return { sessionId: data.sessionId, article: data.article, wsEndpoint: data.wsEndpoint };
  ```
  > 참고: 확장 인입(content[])은 별도 경로. 웹앱은 articleId 유지하되 **필드명만 camel로** 맞추면 됨.
  > 3번과 "camelCase로 통일" 합의 필요(3번 피드백 H3와 연동).

### A2. 퀴즈 제출·용어설명 엔드포인트가 백엔드에 없음 → 항상 mock
- **위치**: `lib/api.ts:224`(`/api/session/{id}/quiz/submit`), `lib/api.ts:244`(`/api/session/{id}/explain`)
- **증상**: 두 경로 모두 3번 백엔드에 **라우트가 없음**(3번엔 `/start,/finish,/result` + WS만). 항상 catch/`!ok` → mock 반환.
- **영향**: 퀴즈 채점·RAG 용어설명이 **실제로는 mock**. 데모에서 "실제 채점/실제 RAG"로 보이지만 아님.
- **수정안**: (a) 퀴즈 채점 → 3번에 엔드포인트 추가 요청하거나 2번 `/api/content-reducer/quiz` 계약에 맞춤, (b) 용어설명 → **2번 단어 lookup(무료)** 경로로 연결(EXTENSION_DESIGN §10 2번 ③). 최소한 "현재 mock"임을 팀에 명시.

---

## 🟡 Medium — 정합성 / 로직 충돌

### A3. 넛지 임계값이 프론트↔백엔드 불일치
- **위치**: `NudgeController.tsx:27~32` (80/60/40) vs 3번 `cognitive_care.determine_intervention` (75/50/30)
- **증상**: 로컬(mock) 판정은 `>=80 none / >=60 soft / >=40 medium / <40 hard`, 백엔드(WS 연결 시)는 `75/50/30`. **같은 focusScore에서 넛지 단계가 달라짐.**
- **영향**: mock 데모와 실연동 데모의 개입 타이밍이 다름 → 리허설·심사에서 혼선.
- **수정안**: 임계값을 한 곳(계약 문서)에서 확정하고 양쪽 동기화. 권장은 백엔드 기준(75/50/30).

### A4. `useScoreEngine`가 API 최종 점수를 덮어씀(clobber) + 과도한 갱신
- **위치**: `lib/useScoreEngine.ts:116~122` + `ReadingPage.tsx:113~134`(session_end 시 API 결과 주입)
- **증상**: `session_end`에서 `api.getSessionResult`로 **권위 있는 서버 literacyScore**를 scoreStore에 넣는데, `useScoreEngine`의 `[focusScore]` 이펙트가 이후에도 계속 **로컬 근사식으로 `setLiteracyScore`를 호출** → 서버 값이 로컬 값으로 **덮어써질 수 있음**. 또 focus/quiz 변할 때마다 매번 setLiteracyScore → 리렌더 churn.
- **영향**: 최종 화면의 Literacy Score가 서버값↔로컬값 사이에서 흔들림.
- **수정안**: 세션 종료(완독/`session_end`) 후에는 로컬 엔진을 정지하거나(`if (isFinished) return`), 서버 결과 수신 플래그를 두어 로컬 계산이 덮어쓰지 않게 가드.

### A5. 스크롤 WS 이벤트에 스로틀 없음 → 백엔드 폭주
- **위치**: `ReadingPane.tsx:129~152` (`handleScroll`이 매 스크롤 틱마다 `sendScrollEvent`)
- **증상**: `onScroll`마다 WS로 이벤트 전송. 3번 `ws.py`는 **메시지마다 Redis 전건 `lrange` + focus 재계산 + 응답** → 세션이 길어질수록 O(n²). 클라도 서버도 부하.
- **영향**: 실연동 시 렉·넛지 지연·불필요 트래픽. (확장 config엔 `SCROLL_THROTTLE_MS=120`이 있는데 웹앱엔 없음.)
- **수정안**: `handleScroll`에 throttle(예: 120~200ms) 적용. store 업데이트(progress)는 즉시, WS 전송만 스로틀.

### A6. `session_end` 커맨드를 백엔드가 보내지 않음
- **위치**: `ReadingPage.tsx:111~141` (`case 'session_end'`)
- **증상**: 3번 `ws.py`는 `to_intervention_command`(nudge/quiz/highlight/score_update)만 전송하고 **`session_end`를 emit하지 않음**. → 최종 결과 조회 트리거가 실연동에서 **발화 안 됨**.
- **영향**: 완독 후 대시보드 동기화가 mock에서만 동작.
- **수정안**: 완독 판정(progress>=100)에서 `getSessionResult`를 직접 호출하도록 바꾸거나, 3번이 종료 시 `session_end`를 보내도록 계약 합의.

---

## 🟢 Low — 개선/확인

- **A7. `useScoreEngine`의 `Math.random()` 기준선**(`useScoreEngine.ts:88`): "케어 전(before)" 값이 매번 랜덤 → 차트가 실행마다 달라짐. 데모 재현성 위해 고정 시드/상수 권장.
- **A8. focusStore 초기 `focusScore=85` vs reset `100`**(`focusStore.ts:29,45`): 초기·리셋 값 불일치. 의도 아니면 통일.
- **A9. dwell 이벤트가 "이전 단락" 인덱스 전송**(`ReadingPane.tsx:183` `String(currentParagraph.current)`): 진입 단락이 아니라 직전 단락 id를 보냄. 라벨링 혼동 소지(집중 계산엔 영향 적음).
- **A10. `types/shared.ts`가 실제 백엔드 계약과 별개로 존재**: `ReadingSessionState`(camel, articleId 등)와 3번 실제 필드가 다름. 참고용 타입임을 명시하거나 계약 확정본으로 동기화.
- **A11. `startSession` 하드코딩**(`ReadingPage.tsx:48~51` `articleId:'default-article', userId:'user-001'`): 데모엔 무방하나 실사용 시 주입 필요.

---

## 통합(1번 관점) 우선순위

1. **A1 스키마 정합** — 이게 안 되면 "실연동"이 전부 mock. 3번과 **camelCase 통일**(3번 피드백 H3와 한 세트). 최우선.
2. **A5 스크롤 스로틀** — 실연동 부하/지연 직결. 한 줄로 큰 효과.
3. **A4 점수 clobber / A6 session_end** — 최종 점수 표시 안정화.
4. **A2 퀴즈·용어 엔드포인트** — 실제 채점/RAG로 승격(또는 "mock임" 명시).
5. **A3 임계값 통일** — 데모 일관성.
6. 나머지(A7~A11) 재현성·위생.

> 참고: 3번 백엔드도 별도 피드백을 전달했습니다(`FEEDBACK_TO_ROLE3_FROM_ROLE1.md`).
> **A1(4번)과 3번 H3/H4는 같은 "camelCase·계약 정합" 이슈**이니 두 역할이 함께 맞추면 한 번에 해결됩니다.
> 계약 확정은 1번에 공지 바랍니다.
