// 공용 개입 오버레이 (웹 · PDF 뷰어 공용) — window.ALC_Overlay
//
// 페이지 CSS와 충돌하지 않도록 Shadow DOM으로 격리한다.
// create() → { toast, badge, clear }. 넛지/하이라이트/퀴즈 안내는 toast, 집중도는 badge.
window.ALC_Overlay = (() => {
  const TAGS = { nudge: "집중", highlight: "하이라이트", quiz: "퀴즈" };

  function create() {
    let host = null;
    let root = null;

    function ensure() {
      if (host) return;
      host = document.createElement("div");
      host.id = "alc-overlay-host";
      root = host.attachShadow({ mode: "open" });
      root.innerHTML = `
        <style>
          .toast{position:fixed;right:20px;bottom:64px;max-width:280px;
            padding:14px 16px;border-radius:14px;background:#1a1a2e;color:#fff;
            font:14px/1.5 "Pretendard",-apple-system,"Segoe UI",sans-serif;
            box-shadow:0 8px 30px rgba(0,0,0,.25);z-index:2147483647;
            opacity:0;transform:translateY(8px);transition:.25s}
          .toast.show{opacity:1;transform:translateY(0)}
          .toast .tag{display:inline-block;font-size:11px;font-weight:700;
            padding:2px 8px;border-radius:999px;margin-bottom:6px;background:#5b6cff}
          .toast.highlight .tag{background:#00b894}
          .toast.quiz .tag{background:#e17055}
          .badge{position:fixed;right:20px;bottom:20px;padding:8px 12px;
            border-radius:999px;background:#5b6cff;color:#fff;font:600 12px sans-serif;
            z-index:2147483647}
        </style>`;
      (document.documentElement || document.body).appendChild(host);
    }

    function toast(message, kind = "nudge") {
      ensure();
      const el = document.createElement("div");
      el.className = `toast ${kind}`;
      el.innerHTML = `<span class="tag">${TAGS[kind] || "케어"}</span><div>${message}</div>`;
      // 토스트끼리만 교체하고 집중도 배지(.badge)는 유지 — 배지 위에 겹쳐 쌓인다.
      root.querySelectorAll(".toast").forEach((n) => n.remove());
      root.appendChild(el);
      requestAnimationFrame(() => el.classList.add("show"));
      setTimeout(() => el.remove(), 5000);
    }

    function badge(focusScore) {
      if (focusScore == null) return;
      ensure();
      root.querySelectorAll(".badge").forEach((n) => n.remove());
      const el = document.createElement("div");
      el.className = "badge";
      el.textContent = `집중도 ${Math.round(focusScore)}`;
      root.appendChild(el);
    }

    function clear() {
      if (host) host.remove();
      host = null;
      root = null;
    }

    return { toast, badge, clear };
  }

  return { create };
})();
