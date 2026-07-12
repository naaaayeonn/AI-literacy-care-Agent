// 본문 기준 읽기 진행률 (웹 공용) — window.ALC_Progress
//
// 페이지 전체(scrollY/scrollHeight)가 아니라 **본문 문단이 실제로 화면에 머문 비율**로
// 진행률을 잰다(편지 §4). 본문 + 댓글 + 광고 + 푸터가 섞인 페이지 높이 대신,
// content 추출에 쓴 문단 DOM 노드만 관찰하므로 "본문 90% 읽음 / 본문 끝"을 정확히 안다.
//
// 규칙:
//   - IntersectionObserver로 각 문단의 뷰포트 체류를 관찰.
//   - 문단이 화면에 누적 체류(dwell) ≥ max(800ms, 글자수 × 30ms) 이면 readSet에 추가.
//     ("스쳐 지나감"은 dwell 미달로 제외 → 빠른 스크롤 위조 방지)
//   - getProgress() = readSet.size / 문단수  (본문 기준 0~1, 1.0 = 본문 끝)
//   - getReadChunkIndex() = 지금 가장 크게 보이는 문단 인덱스(없으면 마지막으로 읽은 문단)
//
// create({ getElements }) → { getProgress, getReadChunkIndex, detach }
//   getElements: 관찰할 문단 노드 배열을 돌려주는 함수(인덱스 = content[]/chunk 인덱스와 정렬).
//   최초 getProgress/getReadChunkIndex 호출 때 노드를 스냅샷해 관찰을 시작한다(지연 초기화).
window.ALC_Progress = (() => {
  const MIN_DWELL_MS = 800;
  const MS_PER_CHAR = 30;
  const TICK_MS = 400;

  function create({ getElements }) {
    let observer = null;
    let ticker = null;
    let states = []; // [{ el, len, threshold, dwellMs, visibleSince, ratio, engaged }]
    const readSet = new Set();

    function thresholdFor(el) {
      const len = (el.innerText || el.textContent || "").trim().length;
      return { len, ms: Math.max(MIN_DWELL_MS, len * MS_PER_CHAR) };
    }

    // 문단이 "읽히는 중"인지: 짧은 문단은 절반 이상, 뷰포트보다 큰 문단은 뷰포트 절반 이상 노출.
    function isEngaged(entry, elHeight) {
      if (!entry.isIntersecting) return false;
      const vh = (entry.rootBounds && entry.rootBounds.height) || window.innerHeight || 1;
      const shown = entry.intersectionRect.height;
      return shown >= 0.5 * Math.min(elHeight || vh, vh);
    }

    function ensure() {
      if (observer || typeof IntersectionObserver === "undefined") return states.length > 0;
      const els = (getElements() || []).filter(Boolean);
      if (!els.length) return false;

      states = els.map((el) => {
        const { len, ms } = thresholdFor(el);
        return { el, len, threshold: ms, dwellMs: 0, visibleSince: null, ratio: 0, engaged: false };
      });
      const indexOf = new Map(states.map((s, i) => [s.el, i]));

      observer = new IntersectionObserver(
        (entries) => {
          const now = Date.now();
          for (const entry of entries) {
            const i = indexOf.get(entry.target);
            if (i == null) continue;
            const s = states[i];
            s.ratio = entry.intersectionRatio;
            const engaged = isEngaged(entry, entry.boundingClientRect.height);
            if (engaged && !s.engaged) {
              s.visibleSince = now; // 체류 시작
            } else if (!engaged && s.engaged) {
              if (s.visibleSince != null) s.dwellMs += now - s.visibleSince;
              s.visibleSince = null;
            }
            s.engaged = engaged;
          }
          sweep();
        },
        { threshold: [0, 0.25, 0.5, 0.75, 1] }
      );
      states.forEach((s) => observer.observe(s.el));
      // 화면에 계속 머무는 문단은 IO 콜백이 안 오므로 주기적으로 dwell을 누적한다.
      ticker = setInterval(sweep, TICK_MS);
      return true;
    }

    // 현재 체류 중인 문단의 dwell을 갱신하고 임계 넘으면 read로 확정.
    function sweep() {
      const now = Date.now();
      for (let i = 0; i < states.length; i++) {
        const s = states[i];
        if (s.engaged && s.visibleSince != null) {
          s.dwellMs += now - s.visibleSince;
          s.visibleSince = now;
        }
        if (!readSet.has(i) && s.dwellMs >= s.threshold) readSet.add(i);
      }
    }

    function getProgress() {
      if (!ensure()) return 0;
      sweep();
      return states.length ? Math.min(1, readSet.size / states.length) : 0;
    }

    function getReadChunkIndex() {
      if (!ensure()) return null;
      // 지금 가장 크게 보이는 문단(체류 중) 우선, 없으면 마지막으로 읽은 문단.
      let best = -1;
      let bestRatio = 0;
      for (let i = 0; i < states.length; i++) {
        if (states[i].engaged && states[i].ratio >= bestRatio) {
          bestRatio = states[i].ratio;
          best = i;
        }
      }
      if (best >= 0) return best;
      return readSet.size ? Math.max(...readSet) : null;
    }

    function detach() {
      if (observer) observer.disconnect();
      if (ticker) clearInterval(ticker);
      observer = null;
      ticker = null;
    }

    return { getProgress, getReadChunkIndex, detach };
  }

  return { create };
})();
