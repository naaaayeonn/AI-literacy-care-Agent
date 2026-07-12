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
    getReadChunkIndex,
    onEvent,
    scrollTarget = window,
    scrollThrottleMs = 120,
    idleMs = 0,
  }) {
    // 본문 기준 진행률(§4)이 제공되면 "지금 읽는 문단 인덱스"를 이벤트에 함께 싣는다.
    const readChunkIndex = () => {
      if (!getReadChunkIndex) return null;
      const idx = getReadChunkIndex();
      return typeof idx === "number" ? idx : null;
    };
    const startedAt = Date.now();
    const now = () => Date.now() - startedAt; // 세션 상대 ms(정수)
    let lastScrollAt = 0;
    let lastOffset = null; // 직전 스크롤 오프셋(px) — px/ms 속도 계산용
    let lastPosition = null; // 직전 진행률(0~1) — %/초 속도 계산용
    let idleTimer = null;

    // 실제로 스크롤된 요소를 찾는다. scroll 이벤트는 버블링이 안 되므로 capture로 듣고,
    // e.target(스크롤된 요소)에서 오프셋을 읽어야 내부 컨테이너 스크롤도 잡힌다.
    // 문서 스크롤이면 e.target이 document → scrollingElement로 환산.
    function currentScroller(e) {
      const target = e && e.target;
      if (!target || target === document || target === window ||
          target === document.documentElement || target === document.body) {
        return document.scrollingElement || document.documentElement || document.body;
      }
      return target;
    }

    function emit(type, extra) {
      onEvent({ type, timestamp_ms: now(), ...extra });
      resetIdle();
    }

    function onScroll(e) {
      const t = Date.now();
      // 스로틀: 직전 emit 후 throttle ms 이내면 건너뜀. 단 첫 스크롤은 반드시 통과시키고
      // lastScrollAt을 갱신한다. (버그: 예전엔 lastScrollAt=0 → (lastScrollAt||t)=t →
      //  interval이 항상 0 → 항상 return → lastScrollAt이 영영 갱신 안 돼 스크롤이 통째로 차단됐음.)
      if (lastScrollAt && t - lastScrollAt < scrollThrottleMs) return; // 과도 전송 방지
      const interval = lastScrollAt ? t - lastScrollAt : 0;
      lastScrollAt = t;

      // 백엔드로 보내는 진행률은 주입된 getProgress 유지(웹=scrollY/max, PDF=page/total).
      const position = clamp01(getProgress());

      // 속도 계산용 오프셋/진행률 — 실제 스크롤된 요소 기준(내부 컨테이너 스크롤 대응).
      const scroller = currentScroller(e);
      const offset =
        scroller && typeof scroller.scrollTop === "number"
          ? scroller.scrollTop
          : window.scrollY || window.pageYOffset || 0;
      let scrollProgress = position;
      if (scroller) {
        const maxScroll = scroller.scrollHeight - scroller.clientHeight;
        if (maxScroll > 0) scrollProgress = clamp01(offset / maxScroll);
      }

      // 스크롤 속도 — 첫 스크롤은 기준이 없어 0.
      //  velocity: 이동 픽셀 / 경과 ms (px/ms) — 3번 calculate_focus_score가 읽는 필드
      //  speed_pct_s: 진행률 변화(%) / 경과 초 (%/초) — 모니터 표시용
      let pxPerMs = 0;
      let pctPerSec = 0;
      if (interval > 0) {
        if (lastOffset != null) pxPerMs = Math.abs(offset - lastOffset) / interval;
        if (lastPosition != null) pctPerSec = (Math.abs(scrollProgress - lastPosition) * 100) / (interval / 1000);
      }
      lastOffset = offset;
      lastPosition = scrollProgress;
      // velocity(px/ms)는 3번 집중도 로직이 읽는 계약 필드. speed_pct_s는 모니터 표시용.
      const idx = readChunkIndex();
      emit("scroll", {
        position,
        duration_ms: interval,
        velocity: Math.round(pxPerMs * 100) / 100,
        speed_pct_s: Math.round(pctPerSec * 10) / 10,
        ...(idx != null ? { readChunkIndex: idx } : {}),
      });
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
      idleTimer = setTimeout(() => {
        const idx = readChunkIndex();
        emit("pause", {
          position: clamp01(getProgress()),
          ...(idx != null ? { readChunkIndex: idx } : {}),
        });
      }, idleMs);
    }

    function attach() {
      // capture: true — scroll은 버블링이 안 되므로 캡처 단계로 들어야 내부 컨테이너 스크롤까지 잡는다.
      scrollTarget.addEventListener("scroll", onScroll, { passive: true, capture: true });
      window.addEventListener("blur", onBlur);
      window.addEventListener("focus", onFocus);
      document.addEventListener("visibilitychange", onVisibility);
      resetIdle();
    }

    function detach() {
      scrollTarget.removeEventListener("scroll", onScroll, { capture: true });
      window.removeEventListener("blur", onBlur);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
      if (idleTimer) clearTimeout(idleTimer);
    }

    return { attach, detach };
  }

  return { create };
})();
