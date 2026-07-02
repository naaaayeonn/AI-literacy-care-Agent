// 공용 읽기행동 트래커 (웹 · PDF 뷰어 공용) — window.ALC_Tracker
//
// 전송·본문추출을 모른다. DOM 이벤트만 잡아 **정규화된 이벤트**를 onEvent로 흘린다.
// 정규화 스키마(API_CONTRACT §9-2): { type, timestamp_ms, position?, duration_ms? }
//   - timestamp_ms: 세션 시작 기준 ms (epoch 아님)
//   - position: 0.0~1.0 읽기 진행률 (getProgress()가 공급 — 웹=scrollY/max, PDF=page/total)
//   - duration_ms: scroll의 경우 직전 스크롤과의 간격(빠른 스크롤 감점에 사용)
//
// 재사용 포인트: 스크롤 대상(target)과 진행률(getProgress)만 주입하면 웹·PDF 동일 동작.
window.ALC_Tracker = (() => {
  const clamp01 = (n) => Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));

  function create({
    getProgress,
    onEvent,
    scrollTarget = window,
    scrollThrottleMs = 120,
    idleMs = 0,
  }) {
    const startedAt = Date.now();
    const now = () => Date.now() - startedAt; // 세션 상대 ms(정수)
    let lastScrollAt = 0;
    let idleTimer = null;

    function emit(type, extra) {
      onEvent({ type, timestamp_ms: now(), ...extra });
      resetIdle();
    }

    function onScroll() {
      const t = Date.now();
      const interval = t - (lastScrollAt || t);
      if (interval < scrollThrottleMs) return; // 과도 전송 방지
      lastScrollAt = t;
      emit("scroll", { position: clamp01(getProgress()), duration_ms: interval });
    }

    function onBlur() {
      emit("blur", {});
    }
    function onFocus() {
      emit("focus", {});
    }
    function onVisibility() {
      if (document.hidden) onBlur();
      else onFocus();
    }

    // idle(무동작) N초 → pause 이벤트 → 서버가 넛지로 응답(ADR-002 idle 넛지)
    function resetIdle() {
      if (!idleMs) return;
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(
        () => emit("pause", { position: clamp01(getProgress()) }),
        idleMs
      );
    }

    function attach() {
      scrollTarget.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("blur", onBlur);
      window.addEventListener("focus", onFocus);
      document.addEventListener("visibilitychange", onVisibility);
      resetIdle();
    }

    function detach() {
      scrollTarget.removeEventListener("scroll", onScroll);
      window.removeEventListener("blur", onBlur);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
      if (idleTimer) clearTimeout(idleTimer);
    }

    return { attach, detach };
  }

  return { create };
})();
