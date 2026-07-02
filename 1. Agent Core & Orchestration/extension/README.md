# AI 리터러시 케어 — 크롬 확장 (웹페이지 MVP)

파일 업로드 없이, 크롬에서 읽는 글의 읽기 행동을 측정하고 집중이 떨어지면
부드럽게 개입한다. 기존 백엔드/오케스트레이터 계약을 그대로 재사용한다.

## 구조

```
extension/
├─ manifest.json            MV3 매니페스트
├─ config.js                백엔드 주소·임계값 (전역 설정)
├─ background/
│  └─ service_worker.js     상태 기본값·토글 로그 (가벼운 코디네이터)
├─ popup/
│  ├─ popup.html/css/js     on/off 토글 UI
├─ shared/                  ★ 웹·PDF 공용 모듈
│  ├─ tracker.js            읽기행동 이벤트 캡처(전송·추출 무관)
│  ├─ overlay.js            Shadow DOM 개입 오버레이(toast/badge)
│  └─ session_client.js     세션 수명 + REST 전송(ADR-001)
└─ content/
   ├─ content_script.js     웹 어댑터(본문추출·진행률만) → shared 주입
   └─ overlay.css           (Shadow DOM 사용, 의도적 빈 파일)
```

> shared/ 3종은 웹과 PDF 뷰어가 **그대로 재사용**한다. content_script(웹)와 후속
> pdf/viewer.js(PDF)는 각자 `extract()`·`getProgress()`만 주입하고 나머지는 공용이다.

## 동작 흐름

1. 팝업에서 **on** → `chrome.storage.local.enabled = true`
2. content script가 페이지마다 "읽을 만한 글"인지 판정 (본문 길이 임계값)
3. 일정 시간 머무르면 `POST /api/session/start`(본문 `content[]`) → `sessionId` 수신
4. tracker가 읽기행동 이벤트를 캡처 → 큐에 모아 **배치 `POST /events`**(REST, ADR-001)
5. 응답의 개입 명령(`{type, payload}`)을 우측 하단 토스트/배지로 렌더
6. 탭 이탈/숨김 → `GET /result`로 세션 종료·최종 점수 계산

## 백엔드 계약 (정본: `docs/API_CONTRACT.md` §9)

| 방향 | 형식 |
|---|---|
| 세션 시작 | `POST /api/session/start { userId, articleId, source, content[] }` → `{ sessionId, ... }` |
| 이벤트 송신 | `POST /api/session/{id}/events { session_id, events:[{ type, timestamp_ms, position, duration_ms }] }` |
| 개입 수신 | 위 응답 `{ type:"nudge"\|"highlight"\|"quiz"\|"score_update", payload:{ nudgeLevel, nudgeMessage, focusScore } }` |
| 세션 결과 | `GET /api/session/{id}/result` → 최종 점수(성장 그래프용) |

> tracker가 이미 **정규화 스키마**로 보낸다(§9-2): `position`(0~1), `duration_ms`(스크롤 간격
> → 빠른 스크롤 300ms 미만 감점). 전송은 WS가 아니라 **REST 배치 flush**(ADR-001).
> 백엔드 alias는 `backend/app/api/extension_session.py`(테스트 통과).

## 설치 (개발용)

1. 백엔드 실행: `uvicorn backend.app.main:app --reload` (localhost:8000)
2. 크롬 → `chrome://extensions` → **개발자 모드** 켜기
3. **압축해제된 확장 프로그램을 로드** → 이 `extension/` 폴더 선택
4. 툴바 아이콘 클릭 → **on** → 아무 기사 페이지에서 스크롤/탭 전환 테스트
5. 콘솔(F12)에서 `[ALC]` 로그와 우측 하단 넛지 확인

## TODO (후속)

- **PDF 뷰어(pdf/viewer.js)** — shared 3종 재사용 + pdf.js용 `extract()`/`getProgress()` 주입 (EXTENSION_DESIGN §9)
- 본문 추출 품질: `@mozilla/readability` 끼우기 (지금은 `<p>` 휴리스틱)
- 팝업 온보딩: 개인정보 동의 화면 + 문서 열기(로컬 pdf.js) (EXTENSION_DESIGN §13)
- 단락 단위 dwell(`IntersectionObserver`)로 집중 저하 단락 추적
- 세션 결과를 대시보드에 기록(현재는 `GET /result` 호출만)
- CORS: 백엔드에 `chrome-extension://` 오리진 허용 (3번)
