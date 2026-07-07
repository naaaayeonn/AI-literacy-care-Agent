# Chrome 확장 프로그램 설계 — "어디서나 읽기 케어"

> 계획 외 추가 기능. 파일 업로드 없이 **크롬에서 읽는 모든 글**에 대해 읽기 행동을
> 측정·개입·점수화한다. on/off 토글로 켜두면 백그라운드에서 상시 동작.
> 범위: **① 웹페이지 + ② PDF(pdf.js 자체 뷰어)**. 두 경우 모두 스크롤 속도·집중도
> 수집, 창 위 퀴즈, 단어 뜻 툴팁이 동작한다. PDF 상세 설계는 **§9~§11**에 있다.
>
> ⚠️ **"크롬 밖 다른 PDF뷰어·모든 앱 창"은 본 문서 범위 밖**(네이티브 데스크톱
> 에이전트 별도 트랙). 크롬 기본 PDF뷰어는 PDFium 플러그인이라 접근 불가 →
> **우리 pdf.js 뷰어로 자동 전환**해서 해결한다(§9-1).

## 1. 핵심 통찰 — 코어는 거의 안 바뀐다

오케스트레이터는 이벤트의 **출처를 가리지 않는다.**
- 입력: `reading_events`(scroll/pause/blur/focus) + 글 텍스트
- 출력: `to_intervention_command()`(넛지/하이라이트) + `to_session_result()`(score)

이 이벤트가 웹앱에서 오든 확장에서 오든 동일하다. 따라서 이번 작업은
**코어 교체가 아니라 "새 입력원(확장) 추가"** 다. 기존 WS 계약과 변환 어댑터를
거의 그대로 재사용한다.

## 2. 웹앱(apps/web)과의 관계

| 컴포넌트 | 역할 |
|---|---|
| **크롬 확장** | 주력 — 실제 읽기 측정 + 라이브 넛지 오버레이 |
| **웹 대시보드** | 공용 — 점수/성장/배지 확인 (기존 GrowthDashboard 재사용) |
| **웹 읽기 화면** | 무설치 데모 폴백 — 심사위원이 확장 미설치 시 시연용 |

읽기 UX를 양쪽에서 중복 유지하지 않는다: 확장=주력, 웹읽기=데모용, 대시보드=공용.

## 3. 아키텍처

```
[크롬 확장 (Manifest V3)]
  ├─ popup/         on/off 토글, 현재 세션 상태
  ├─ background/    service worker: 세션 수명·storage 상태
  └─ content/       페이지 주입:
        ├─ Readability.js  본문 추출(광고·메뉴 제거)
        ├─ tracker         읽기행동 이벤트 캡처
        ├─ ws client       WebSocket 송수신
        └─ overlay (Shadow DOM)  넛지/하이라이트/퀴즈 UI
            │
            │  POST /api/session/start  (페이지 텍스트)
            │  WS   /ws/reading/{id}    (이벤트 ↔ 개입)
            │  GET  /api/session/{id}/result
            ▼
[3번 백엔드] ──→ [1번 오케스트레이터] ──→ [2번 Content Reducer]
```

## 4. 확장 ↔ 백엔드 계약

### 4-1. 기존 계약 재사용

> ⚠️ **전송방식은 ADR-001(§12)로 REST 확정** — 아래 "WS 그대로 사용" 전제는 **대체됨**.
> 이벤트/개입 왕복은 `POST /events`(이벤트 구동) + 응답 개입. 결과 REST(`/result`)는 유효.
- WS `/ws/reading/{session_id}`: 이벤트 스키마(`ReadingBehaviorEvent`)·개입 응답
  (`to_intervention_command`)을 **그대로** 사용. → `FRONTEND_INTEGRATION_GUIDE.md` 참고.
- 결과 `GET /api/session/{id}/result`: `to_session_result` 그대로.

### 4-2. 신규 — 페이지 텍스트로 세션 시작
웹앱은 미리 업로드된 `articleId`로 시작하지만, 확장은 **추출한 본문**을 넘긴다.
`/api/session/start`를 확장해 둘 다 받게 한다(택일).

```jsonc
// POST /api/session/start  (확장용 필드)
{
  "userId": "u_123",
  "source": { "url": "https://...", "title": "...", "type": "web" },
  "content": ["문단1", "문단2", "..."]   // Readability 추출 본문
  // (웹앱은 기존처럼 articleId 사용)
}
// 응답은 기존과 동일: { sessionId, article, wsEndpoint }
```
백엔드 처리: `content` → 2번 Content Reducer(chunks/simplified/terms/difficulty)
→ `create_initial_state` → session_id 발급.

## 5. 세션 수명 (on/off + 백그라운드)

```
[확장 off] → 아무 동작 안 함
[확장 on]  → chrome.storage.local.enabled = true
   페이지 로드 → content script 주입
   Readability "읽을 만한 글" 판정?
      └ 예 → 대기
          사용자 N초 이상 체류/스크롤 → 세션 시작(POST start) + WS 연결
              이벤트 스트리밍 → 실시간 focus → 넛지 오버레이
          탭 이탈/닫기/visibility hidden 지속 → 세션 종료
              → GET result → 점수 계산 → 대시보드 기록
```

> **MV3 현실**: service worker는 상시 떠 있는 데몬이 아니라 이벤트로 자고 깬다.
> 이 용도엔 충분 — 탭/네비게이션 이벤트마다 깨어나 모니터링하면 체감은 "항상 켜짐".
> 진짜 24/7 프로세스는 불필요.

## 6. 역할 분담 (1번 경계)

| 작업 | 담당 | 1번(나) 관여 |
|---|---|---|
| 오케스트레이터/세션 수명/score | **1번** | 직접 |
| 확장↔백엔드 계약, page-ingestion 계약 | **1번** | 직접 정의 |
| `/api/session/start` 확장(content 수용) | 3번 | 계약 제공·검증 |
| 본문 추출(Readability 통합) | 2번/확장 | terms·chunks 계약 |
| 확장 UI(popup/오버레이/tracker) | 4번 프론트 | 이벤트·개입 JSON 계약 제공 |
| 확장 골격 프로토타입 | 1번 리드 가능 | 통합 글루로 초기 골격 |

요약: **1번은 "확장이 붙을 수 있는 계약·세션 수명·백엔드 글루"까지.**
확장 UI 완성은 4번, 본문 추출은 2번과 협업.

## 7. 단계별 계획

1. **MVP (웹페이지)**: on/off + 읽기행동 캡처 + 개입 오버레이(넛지/퀴즈/단어뜻).
   기존 백엔드/오케스트레이터 재사용. → 데모 임팩트 확보.
2. **PDF 지원 (pdf.js 자체 뷰어)**: PDF 링크를 우리 뷰어로 가로채 렌더 →
   웹페이지와 **동일한** 트래커/오버레이 재사용. 상세 §9~§11. → "논문 읽기" 데모의 핵심.
3. **세션 자동감지 정교화**: 읽기 판정·집중 가중치 튜닝.
4. **(범위 밖·후속) 네이티브 에이전트**: 크롬 밖 다른 뷰어/모든 창. 별도 트랙.

## 8. 리스크

| 리스크 | 완화 |
|---|---|
| 스캔(이미지) PDF엔 글자 레이어 없음 | MVP는 "글자 레이어 있는 PDF"만. OCR(Tesseract.js·무료)은 후속(§11) |
| 페이지 CSS와 오버레이 충돌 | Shadow DOM 격리 |
| "읽기" 오판(브라우징과 구분) | 체류시간+본문 길이 임계값 |
| 확장 심사/설치 장벽(데모) | 웹 읽기 화면을 무설치 폴백으로 유지 |
| MV3 service worker 수명 | 이벤트 기반 설계, 상태는 storage에 |
| PDF 리다이렉트 오작동(다운로드 링크 등) | main_frame·`.pdf`만 조건화, on/off·사이트 제외 규칙 |
| 대용량 PDF 렌더 성능 | 페이지 지연 렌더(보이는 페이지만), textLayer 필요 시 생성 |
| 범위 확대로 일정 압박 | 트래커/오버레이 **웹·PDF 공용화**로 중복 제거, 코어 불변 |

---

## 9. PDF 지원 — pdf.js 자체 뷰어 (상세 설계)

> ✅ **구현 완료** (2026-07-03) — `extension/pdf/viewer.{html,js,css}` + `vendor/pdfjs`
> (pdfjs-dist@4.10.38, Apache-2.0 번들). 가로채기(§9-4)·텍스트추출(§9-5)·집중신호(§9-6)
> 동작. 웹과 동일한 shared 모듈 재사용. 단어 툴팁(§9-7)은 후속.

### 9-1. 왜 기본 뷰어로는 안 되고, 왜 pdf.js면 되는가

크롬 **기본 PDF뷰어**는 PDFium(네이티브 플러그인)이 페이지를 "그림처럼" 그린다.
→ 확장이 **글자·좌표·스크롤에 접근 불가** = 스크롤 속도·퀴즈·단어 뜻 전부 불가.

**pdf.js**(Mozilla)는 PDF를 **JavaScript로 다시 그려 DOM으로 되돌린다.** 페이지를
`<canvas>`로 그리고 그 위에 **단어마다 `<span>` 텍스트 레이어**를 좌표 맞춰 깐다.
→ PDF가 "일반 웹페이지"가 되어 §웹페이지와 **똑같은** 트래커/오버레이를 그대로 쓴다.

핵심: **사용자 경험은 기본 뷰어와 동일**(PDF 링크 클릭 → 열림, 업로드 없음).
바뀌는 건 "누가 렌더하느냐"뿐 — 크롬 대신 우리가 렌더해서 만질 수 있게 만든다.

| 읽는 방식 | 스크롤 속도 | 창 위 퀴즈 | 단어 뜻 | 사용자 경험 |
|---|---|---|---|---|
| 크롬 웹페이지 | ✅ | ✅ | ✅ | 그대로 |
| 크롬 기본 PDF뷰어 | ❌ | ❌ | ❌ | 그대로 |
| **우리 pdf.js 뷰어** | ✅ | ✅ | ✅ | **그대로**(자동 전환) |

### 9-2. 동작 흐름

```
PDF 링크 클릭 (https://….pdf 또는 file://….pdf)
  └ declarativeNetRequest 규칙이 main_frame 요청을 가로챔
      → chrome-extension://<id>/pdf/viewer.html?file=<원본 URL>
          ├ pdf.js가 원본 URL을 fetch → 페이지별 canvas + textLayer(<span>) 렌더
          ├ getTextContent()로 본문 추출 → content[] 로 POST /api/session/start
          ├ tracker (웹·PDF 공용): 스크롤 속도·체류·blur/focus → 백엔드
          ├ overlay (웹·PDF 공용): 넛지·퀴즈·단어뜻 툴팁
          └ 단어 hover/click → textLayer span에서 단어 추출 → 용어풀이 요청 → 툴팁
```

### 9-3. 파일 구조 추가

```
extension/
├─ manifest.json              ✅ declarativeNetRequest + web_accessible_resources
├─ vendor/pdfjs/              ✅ pdf.mjs, pdf.worker.mjs (pdfjs-dist@4.10.38, Apache-2.0)
├─ pdf/                       ✅ 구현됨
│  ├─ viewer.html             뷰어 페이지(shared 로드 + module viewer.js)
│  ├─ viewer.js               pdf.js 렌더 + 텍스트추출 + shared 주입(PDF 어댑터)
│  └─ viewer.css
├─ shared/                    ✅ 구현됨 (웹·PDF 공용)
│  ├─ tracker.js              읽기행동 이벤트 캡처(전송·추출 무관, 정규화 스키마 방출)
│  ├─ overlay.js              Shadow DOM 오버레이(toast/badge; 퀴즈/툴팁 후속)
│  └─ session_client.js       세션 수명 + REST 배치 flush 전송(ADR-001)
├─ background/service_worker.js (수정: PDF 리다이렉트 동적 규칙 등록/해제)
└─ content/content_script.js  (수정: shared/tracker·overlay 사용)
```

### 9-4. 가로채기(intercept) 메커니즘

- MV3 `declarativeNetRequest`로 `main_frame`의 `*.pdf` 요청을 우리 뷰어로 redirect.
- 원본 URL을 살려 넘겨야 하므로 **service worker에서 동적 규칙**으로 생성
  (정적 규칙은 확장 id를 못 박아 불편 → `chrome.runtime.getURL`로 조립).

```js
// background/service_worker.js — enabled일 때만 PDF를 우리 뷰어로 리다이렉트
const VIEWER = chrome.runtime.getURL("pdf/viewer.html"); // chrome-extension://<id>/pdf/viewer.html
chrome.declarativeNetRequest.updateDynamicRules({
  removeRuleIds: [1],
  addRules: [{
    id: 1, priority: 1,
    action: { type: "redirect",
      redirect: { regexSubstitution: VIEWER + "?file=\\0" } }, // \\0 = 매치된 원본 URL
    condition: { regexFilter: "^https?://.*\\.pdf($|\\?)", resourceTypes: ["main_frame"] }
  }]
});
// off거나 특정 사이트 제외 시 removeRuleIds로 규칙 해제
```

- `file://` 로컬 PDF: `chrome://extensions`에서 **"파일 URL 접근 허용"** 토글 필요 +
  규칙에 file 스킴 조건 추가.
- **manifest 추가분**:

```jsonc
{
  "permissions": ["storage", "scripting", "declarativeNetRequest"],
  "web_accessible_resources": [{
    "resources": ["pdf/viewer.html", "vendor/pdfjs/*", "shared/*"],
    "matches": ["<all_urls>"]
  }]
}
```

### 9-5. 텍스트 추출 → 세션 시작 (계약 재사용)

- pdf.js `page.getTextContent()` → 텍스트 아이템 배열. y좌표로 줄→문단 재구성,
  하이픈 줄바꿈(`-\n`) 병합, 머리말/꼬리말(반복 라인) 제거.
- 정제한 `content[]`를 **기존 확장 계약** `POST /api/session/start`로 전송.
- 즉 백엔드 관점에선 **"웹이든 PDF든 content[] 받으면 끝"** — 신규 계약 불필요.

### 9-6. 집중 신호(스크롤 속도 등)

- 뷰어 스크롤 컨테이너가 **우리 DOM** → `scroll` 이벤트 정상 발생. 속도 = Δ위치/Δ시간.
- 진행률 = 현재 페이지/총 페이지(또는 scrollTop/scrollHeight).
- blur/focus/visibility, 문단 체류(textLayer에 `IntersectionObserver`) 전부 웹과 동일 tracker 재사용.

### 9-7. 단어 뜻 / 퀴즈 오버레이

- textLayer의 `<span>` 위 hover → `caretRangeFromPoint`로 커서 밑 단어 추출
  → 용어풀이 요청 → 툴팁 표시.
- 퀴즈·넛지: 기존 Shadow DOM overlay 재사용(뷰어 위에 표시). 퀴즈는 모달 형태로 확장.

---

## 10. 역할별 추가 작업 (PDF / pdf.js)

> 원칙: **코어(이벤트→개입→점수)와 계약은 그대로.** 이번 추가는 "새 입력원(PDF) +
> 공용 트래커/오버레이 + 뷰어 UI"뿐. 웹↔PDF 중복을 만들지 않는다.

### 1번 — 오케스트레이터·계약·확장 글루 (리드)
- [ ] `content/content_script.js`의 tracker/overlay를 `shared/`로 분리(웹·PDF 공용화)
- [ ] PDF 인입 계약 확정: pdf.js 추출 `content[]` → `/api/session/start` (기존 계약 재사용 명문화)
- [ ] `manifest.json` 변경 설계(declarativeNetRequest·web_accessible_resources) + 리다이렉트 규칙 스펙
- [ ] **세션 경계 정의**: PDF 열기~닫기/페이지 이탈을 한 세션으로(업로드 없는 환경 규칙)
- [ ] `EXTENSION_INTEGRATION_FIXES.md`의 WS/REST 결정과 정합 유지

### 2번 — Content Reducer·본문추출
- [ ] pdf.js `getTextContent()` → 문단 재구성 로직(줄 병합·하이픈·머리말/꼬리말 제거)
- [ ] 웹=Readability / PDF=pdf.js 두 소스를 **동일한 `content[]` 형태**로 정규화
- [ ] 용어풀이(terms) 계약: 단어 → 뜻. **무료 경로만**(기존 RAG 용어풀이/로컬 사전), 유료 사전 API 금지
- [ ] (선택) 문단별 난이도 태그 → 어려운 문단 우선 개입 데이터 제공

### 3번 — 백엔드 구현
- [ ] `/api/session/start`가 PDF `content[]`도 수용(웹과 동일)하는지 검증
- [ ] 단어 뜻 lookup 응답(있으면) — **무료**(로컬/기존 에이전트)로 제공
- [ ] **CORS**: `chrome-extension://` 오리진 허용(뷰어 페이지가 직접 fetch)
- [ ] WS/REST 실제 서빙은 `EXTENSION_INTEGRATION_FIXES.md`의 1번 결정에 따름

### 4번 — 확장 UI·뷰어
- [ ] `pdf/viewer.html·js·css`: pdf.js로 페이지 렌더(canvas + textLayer), 페이지 네비/툴바 최소 UI
- [ ] 단어 hover **툴팁 UI**, **퀴즈 모달 UI**(overlay 확장)
- [ ] `shared/tracker`·`shared/overlay` 공용 모듈을 뷰어에 연결
- [ ] 뷰어 사용성: 스크롤·확대/축소·(다운로드/인쇄 폴백) — 기본 뷰어 대비 이질감 최소화

---

## 11. 비용 0 원칙 & 라이선스

> **새로 과금되는 요소를 추가하지 않는다.** 외부 유료 서비스·유료 호스팅·유료 API 키 불가.

| 요소 | 무엇 | 라이선스/비용 |
|---|---|---|
| PDF 렌더 | **pdf.js** (Mozilla) | Apache-2.0 · **무료** · 확장에 번들(자체 호스팅, 외부 CDN 불필요) |
| 가로채기·트래킹·오버레이 | 브라우저 내장 API(declarativeNetRequest 등) | 비용 0 |
| 단어 뜻·퀴즈 생성 | 기존 백엔드 에이전트 경로 재사용 | 데모는 stub로 무료 동작. 유료 사전/API 신규 도입 금지 |
| 스캔 PDF OCR (후속) | **Tesseract.js** | Apache-2.0 · 브라우저 로컬 실행 · **무료** · MVP 제외 |

- pdf.js 배포본은 [github.com/mozilla/pdf.js Releases](https://github.com/mozilla/pdf.js/releases)에서
  `pdfjs-<버전>-dist.zip`을 받아 `extension/vendor/pdfjs/`에 넣는다(빌드 불필요).
- LLM 호출이 유료라면 그건 **기존 오케스트레이터 아키텍처 이슈**이지 이번 PDF 추가로 새로
  드는 비용이 아니다. 데모/개발은 stub 경로로 과금 없이 돌린다.

---

## 12. 결정 기록 (ADR)

> 정본은 `EXTENSION_INTEGRATION_FIXES.md`. 여기엔 요약을 둔다.

### ADR-001 — 실시간 전송 방식: REST(event-driven), WS 후속 · 2026-07-03 채택

- **결정**: 확장↔백엔드 이벤트/개입 왕복은 **REST**. 이벤트 발생 시 `POST /events`(배치 flush)
  → **응답에 실린 개입**을 렌더. 고정주기 폴링이 아니라 **이벤트 구동**.
- **이유**: 개입이 전부 행동 반응형이라 서버 push 불요 + 백엔드 REST 이미 구현·테스트 완료
  → 신규작업 0, 비용0·일정(M2 7/6) 충족. idle 넛지는 클라가 `pause` 이벤트로 전송.
- **WS**: 후속 선택("실시간 스트리밍" 폴리시). 계약(`to_intervention_command`)이 전송무관이라 저비용 전환.
- **영향**: §10의 3번 "WS 서빙" 제외 / 4번은 WS 클라이언트 → 배치 flush POST 전환 /
  §4-1 "WS 재사용" 전제는 본 ADR로 대체.
- **기각**: WS 신설(일정 대비 과함, 심사에 전송계층 비노출) · 고정주기 폴링(불필요 트래픽).

### ADR-002 — 사용자 식별=익명 기기 UUID, 문서=로컬 pdf.js, 온보딩=팝업 · 2026-07-03 채택

- **결정**: ① 사용자 = 설치 시 익명 UUID(`chrome.storage`), **로그인 없음** ② "문서 업로드" =
  로컬 PDF를 파일 피커→pdf.js 뷰어로 열기(**서버 저장 없음**) ③ 온보딩(동의+ON/OFF)=팝업 최초 1회.
- **이유**: 마찰 0·비용 0·PII 없음 → 즉시 체험, 익명 ID로도 프로필 누적 성립. 문서 로컬 처리로 업로드 서버 불요.
- **후속·기각**: 구글 OAuth(기기간 동기화 필요 시 후속) · 이메일+비번 자체구현(기각) · 서버 업로드 보관(기각).
- 상세: §13 · 정본 `EXTENSION_INTEGRATION_FIXES.md` ADR-002.

---

## 13. 온보딩 & 사용자 식별 (첫 실행)

> ADR-002 확정 반영. 전부 확장 안에서, **비용 0**(익명 로컬 ID + 브라우저 로컬 문서 처리).

### 13-1. 온보딩 플로우 (확장 팝업)

```
설치 → 팝업 최초 오픈
  1) 개인정보 동의 화면  [동의]         (미동의 → 아무 것도 수집 안 함)
       └ consent 저장 + userId(UUID) 생성
  2) ON/OFF 토글 (기본 OFF)
       ON → enabled=true → 크롬에서 "보던 대로" 자동 측정(웹 + PDF 링크→pdf.js 뷰어)
  3) [문서 열기] 버튼 → 로컬 PDF 파일 피커 → pdf.js 뷰어로 렌더
  (재오픈 시: 1) 건너뛰고 현재 세션 상태 + 토글만 표시)
```

### 13-2. 사용자 식별 — 익명 기기 UUID

- 설치 시 `crypto.randomUUID()` → `chrome.storage.local.userId`. 없으면 생성, 있으면 재사용.
- 백엔드 `userId`로 이 값 사용(API_CONTRACT §9-1). **로그인·회원가입 없음.**
- `config.js`의 고정 `USER_ID:"demo_user"`를 이 로직으로 교체.
- 한계: 기기간 동기화·기기 넘는 영속 불가(확장 삭제 시 로컬 소실). 필요 시 구글 OAuth 후속.

### 13-3. 개인정보 동의 (최초 1회)

동의 전에는 **아무 것도 수집하지 않는다.** 동의 화면 고지 내용:

| 항목 | 내용 |
|---|---|
| 수집 | ON인 동안 **읽는 페이지의 본문 텍스트**, 읽기행동(스크롤·체류·이탈·포커스), 퀴즈 응답 |
| 목적 | 집중도·이해도 측정 → 개입(넛지·퀴즈·단어뜻)·성장 추적 |
| 저장/전송 | 로컬(`chrome.storage`) + 백엔드(**익명 userId** 기준). PII 없음 |
| 통제 | 언제든 OFF·데이터 삭제. **OFF면 일절 수집 안 함** |
| 안 하는 것(정직) | 화면 상시 감시 아님(ON+읽을만한 글일 때만) · EEG/카메라 없음 · **크롬 밖 앱 안 봄** |

- 저장: `chrome.storage.local.consent = { version, acceptedAt }`. **동의 버전 갱신 시 재동의.**
- 이 "안 하는 것" 고지는 심사 방어(기획안 §4.3 "❌ 하지 말아야 할 말")와 같은 정직 원칙.

### 13-4. "문서 열기" = 로컬 pdf.js (서버 없음)

- 파일 피커로 고른 PDF `File` → `ArrayBuffer` → pdf.js 렌더. **file:// 권한·업로드 서버 불필요.**
- 이후 흐름은 §9 pdf.js 뷰어와 동일(텍스트 추출 → `content[]` → 세션 시작 → 트래커/오버레이).

### 13-5. 백그라운드 동작 범위 (재확인)

- **크롬 내부 한정.** 다른 탭/창으로 전환해도 각 탭 content script가 측정, service worker는
  탭·네비 이벤트로 깨어남 → 체감 상시. **크롬 밖 앱 위 측정·오버레이는 범위 밖**(네이티브 트랙).

### 13-6. 역할 (온보딩 관련 추가)

- **4번**: 동의 화면 UI + ON/OFF 토글 + 파일 피커 + UUID 생성 로직(팝업)
- **1번**: `consent`/`userId` 상태 스키마(`chrome.storage`) + 백엔드 `userId` 계약 정합
- **3번**: 익명 `userId` 수용(기본값 `anonymous` 이미 있음) + (후속) 데이터 삭제 요청 처리
