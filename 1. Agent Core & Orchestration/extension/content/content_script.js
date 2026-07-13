// AI 리터러시 케어 — content script (웹페이지)
//
// 이제 얇은 "웹 어댑터"다. 공용 로직은 shared/ 모듈이 담당한다:
//   shared/tracker.js        읽기행동 이벤트 캡처
//   shared/overlay.js        Shadow DOM 개입 오버레이
//   shared/session_client.js 세션 수명 + REST 전송(ADR-001)
// 이 파일은 "웹페이지에서 본문을 어떻게 뽑고 진행률을 어떻게 재는지"만 정의한다.
// (PDF는 pdf/viewer.js가 같은 shared 모듈에 pdf.js용 extract/getProgress를 주입한다.)

(() => {
  const CFG = window.ALC_CONFIG;
  if (window.top !== window) return; // 최상위 프레임에서만 동작

  const overlay = window.ALC_Overlay.create();
  let session = null;
  let armTimer = null;

  // content[]로 보낸 본문 문단 DOM 노드(인덱스 = content[]/chunk 인덱스와 정렬).
  // 본문 기준 진행률(§4)이 이 노드들을 관찰한다.
  let articleEls = [];
  const progress = window.ALC_Progress.create({ getElements: () => articleEls });

  // ── 웹 본문 추출 (MVP: <p> 휴리스틱, 후속 @mozilla/readability) ──
  function extract() {
    const rootEl =
      document.querySelector("article") ||
      document.querySelector("main") ||
      document.body;
    articleEls = Array.from(rootEl.querySelectorAll("p")).filter(
      (p) => p.innerText.trim().length > 40
    );
    const content = articleEls.length
      ? articleEls.map((p) => p.innerText.trim())
      : [document.body.innerText.trim()].filter(Boolean);
    return { title: document.title, url: location.href, type: "web", content };
  }

  function isReadable() {
    const text = document.body ? document.body.innerText : "";
    return text.length >= CFG.MIN_READABLE_CHARS;
  }

  // 웹 진행률: 본문 문단 기준(§4). 문단 노드를 못 잡은 경우(전체 body 폴백)만
  // 스크롤 기준으로 강등한다.
  function getProgress() {
    if (articleEls.length) return progress.getProgress();
    const max = document.body.scrollHeight - window.innerHeight;
    return max > 0 ? window.scrollY / max : 0;
  }

  // 지금 읽고 있는 문단 인덱스(§4). 3번이 "어느 문단?"을 알 때 쓴다.
  function getReadChunkIndex() {
    return articleEls.length ? progress.getReadChunkIndex() : null;
  }

  // 설치별 익명 UUID (ADR-002). 없으면 생성해 storage에 보관, 로그인 없음.
  async function getUserId() {
    // 1. 만약 우리 서비스 도메인에 있으면, 사이트의 로그인 세션 ID(local_session_uid)를 감지하여 연동
    if (window.location.hostname.includes("vercel.app") || window.location.hostname.includes("localhost") || window.location.hostname.includes("127.0.0.1")) {
      try {
        const localUid = localStorage.getItem("local_session_uid");
        if (localUid) {
          await chrome.storage.local.set({ userId: localUid });
          return localUid;
        }
      } catch (e) {
        console.warn("[ALC] localStorage 감지 실패:", e);
      }
    }

    // 2. 기존 로직: 저장된 userId가 있으면 반환, 없으면 생성
    const { userId } = await chrome.storage.local.get("userId");
    if (userId) return userId;
    const id =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : "u_" + Date.now() + "_" + Math.floor(Math.random() * 1e6);
    await chrome.storage.local.set({ userId: id });
    return id;
  }

  async function arm() {
    if (session || !isReadable()) return;
    const userId = await getUserId();

    // storage에서 백엔드 URL 읽어서 CFG에 동적 반영 (사용자 지정 Render 서버 대응)
    try {
      const { apiBaseUrl } = await chrome.storage.local.get("apiBaseUrl");
      if (apiBaseUrl) {
        CFG.API_BASE = apiBaseUrl;
        console.log("[ALC] 동적 백엔드 URL 적용:", CFG.API_BASE);
      }
    } catch (e) {
      console.warn("[ALC] 동적 백엔드 URL 로드 실패:", e);
    }

    armTimer = setTimeout(() => {
      session = window.ALC_Session.create({
        cfg: CFG,
        userId,
        extract,
        getProgress,
        getReadChunkIndex,
        overlay,
        scrollTarget: window,
      });
      session.start();
    }, CFG.START_DWELL_MS);
  }

  function disarm() {
    if (armTimer) clearTimeout(armTimer);
    armTimer = null;
    if (session) {
      session.stop();
      session = null;
    }
    progress.detach();
    articleEls = [];
  }

  window.addEventListener("pagehide", () => {
    if (session) session.stop();
  });

  // 집중도 실시간 모니터 토글(다른 창). 사용자 제스처라 팝업 차단을 피한다.
  // Ctrl+Shift+F: 열기/닫기. 세션이 진행 중이면 즉시 이벤트가 흐른다.
  window.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.shiftKey && (e.key === "F" || e.key === "f")) {
      e.preventDefault();
      if (window.ALC_Debug) window.ALC_Debug.toggle();
    }
  });

  // 드래그(선택) 단어 조회 기능 (ADR-002)
  document.addEventListener("mouseup", async (e) => {
    // 오버레이 UI 영역 클릭은 무시
    if (e.target.closest && (e.target.closest("#alc-overlay-host") || e.target.closest(".alc-debug-root"))) {
      return;
    }

    const sel = window.getSelection();
    const text = sel ? sel.toString().replace(/\s+/g, " ").trim() : "";
    if (!text || text.length < 1 || text.length > 40) return;

    // 세션이 활성화된 상태에서만 조회 실행
    if (!session || !session.id) return;

    try {
      // 1. 선택된 단어 주변의 텍스트 컨텍스트 추출
      let anchor = sel.anchorNode;
      let el = anchor && (anchor.nodeType === 3 ? anchor.parentElement : anchor);
      let context = el ? el.innerText || "" : "";
      context = context.slice(0, 300);

      // 2. 오버레이 알림 띄운 뒤 백엔드 API 요청
      overlay.toast("⏳ 단어 뜻을 분석하는 중...", "highlight");

      const res = await fetch(`${CFG.API_BASE}/api/session/${session.id}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ term: text, context }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.definition && data.source !== "not_found") {
          overlay.dict(text, data.definition, data.source);
        } else {
          overlay.dict(text, "사전이나 AI 문맥 분석에서 단어의 뜻을 찾을 수 없습니다.", "");
        }
      } else {
        overlay.dict(text, "서버에서 단어 뜻을 가져오지 못했습니다.", "");
      }
    } catch (err) {
      console.warn("[ALC] 단어 조회 실패:", err);
    }
  });

  async function init() {
    // 웹사이트인 경우 로그인 상태 및 백엔드 서버 주소 항상 동기화
    if (window.location.hostname.includes("vercel.app") || window.location.hostname.includes("localhost") || window.location.hostname.includes("127.0.0.1")) {
      try {
        const localUid = localStorage.getItem("local_session_uid");
        if (localUid) {
          await chrome.storage.local.set({ userId: localUid });
          console.log("[ALC] 웹사이트 사용자 ID 연동 성공:", localUid);
        }
        
        const localBackendUrl = localStorage.getItem("alc_backend_url");
        if (localBackendUrl) {
          await chrome.storage.local.set({ apiBaseUrl: localBackendUrl });
          console.log("[ALC] 웹사이트 백엔드 URL 연동 성공:", localBackendUrl);
        }
      } catch (e) {
        console.warn("[ALC] 웹사이트 상태 연동 실패:", e);
      }
    }

    const { enabled = false } = await chrome.storage.local.get("enabled");
    if (enabled) arm();

    chrome.storage.onChanged.addListener((changes, area) => {
      if (area !== "local" || !changes.enabled) return;
      if (changes.enabled.newValue) arm();
      else disarm();
    });
  }

  init();
})();
