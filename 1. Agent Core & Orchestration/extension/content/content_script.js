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

  // ── 웹 본문 추출 (MVP: <p> 휴리스틱, 후속 @mozilla/readability) ──
  function extract() {
    const rootEl =
      document.querySelector("article") ||
      document.querySelector("main") ||
      document.body;
    const paras = Array.from(rootEl.querySelectorAll("p"))
      .map((p) => p.innerText.trim())
      .filter((t) => t.length > 40);
    const content = paras.length
      ? paras
      : [document.body.innerText.trim()].filter(Boolean);
    return { title: document.title, url: location.href, type: "web", content };
  }

  function isReadable() {
    const text = document.body ? document.body.innerText : "";
    return text.length >= CFG.MIN_READABLE_CHARS;
  }

  // 웹 진행률: 스크롤 위치 / 최대 스크롤 (0~1)
  function getProgress() {
    const max = document.body.scrollHeight - window.innerHeight;
    return max > 0 ? window.scrollY / max : 0;
  }

  // 설치별 익명 UUID (ADR-002). 없으면 생성해 storage에 보관, 로그인 없음.
  async function getUserId() {
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
    armTimer = setTimeout(() => {
      session = window.ALC_Session.create({
        cfg: CFG,
        userId,
        extract,
        getProgress,
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

  async function init() {
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
