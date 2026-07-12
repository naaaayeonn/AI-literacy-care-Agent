// 공용 개입 오버레이 (웹 · PDF 뷰어 공용) — window.ALC_Overlay
//
// 페이지 CSS와 충돌하지 않도록 Shadow DOM으로 격리한다.
// create() → { toast, badge, quiz, clear }. 넛지/하이라이트 안내는 toast, 집중도는 badge,
// O/X 문항은 quiz(quizData, onAnswer)로 카드+버튼을 띄운다(웹·PDF 공용).
window.ALC_Overlay = (() => {
  const TAGS = { nudge: "집중", highlight: "하이라이트", quiz: "퀴즈" };

  // 서버 텍스트(statement/explanation)를 HTML로 주입하지 않도록 이스케이프.
  const esc = (s) =>
    String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

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
          .quiz-card{position:fixed;right:20px;bottom:64px;width:300px;max-width:calc(100vw - 40px);
            padding:16px;border-radius:16px;background:#1a1a2e;color:#fff;
            font:14px/1.55 "Pretendard",-apple-system,"Segoe UI",sans-serif;
            box-shadow:0 10px 36px rgba(0,0,0,.3);z-index:2147483647;
            opacity:0;transform:translateY(8px);transition:.25s}
          .quiz-card.show{opacity:1;transform:translateY(0)}
          .quiz-card .tag{display:inline-block;font-size:11px;font-weight:700;
            padding:2px 8px;border-radius:999px;margin-bottom:8px;background:#e17055}
          .quiz-card .q-stmt{margin:2px 0 12px;font-weight:600}
          .quiz-card .q-btns{display:flex;gap:8px}
          .quiz-card .q-btn{flex:1;padding:10px 0;border:0;border-radius:10px;cursor:pointer;
            font:600 14px sans-serif;color:#fff;transition:.15s}
          .quiz-card .q-o{background:#00b894}
          .quiz-card .q-x{background:#d63031}
          .quiz-card .q-btn:hover{filter:brightness(1.1)}
          .quiz-card .q-btn:disabled{opacity:.5;cursor:default}
          .quiz-card .q-result{margin-top:12px;font-size:13px;line-height:1.5}
          .quiz-card .q-exp{margin-top:6px;opacity:.85}
          .quiz-card.correct{box-shadow:0 0 0 2px #00b894 inset,0 10px 36px rgba(0,0,0,.3)}
          .quiz-card.wrong{box-shadow:0 0 0 2px #d63031 inset,0 10px 36px rgba(0,0,0,.3)}
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

    // O/X 문항 카드. onAnswer(selectedOption:"O"|"X") → Promise<{correct, explanation}>.
    // 답을 고르면 버튼을 잠그고 채점 결과·해설을 보여준 뒤 잠시 후 사라진다.
    function quiz(quizData, onAnswer) {
      if (!quizData || !quizData.statement) return;
      ensure();
      // 진행 중인 토스트/이전 퀴즈는 치우고 카드만 남긴다(배지는 유지).
      root.querySelectorAll(".toast, .quiz-card").forEach((n) => n.remove());

      const card = document.createElement("div");
      card.className = "quiz-card";
      card.innerHTML =
        `<span class="tag">${TAGS.quiz}</span>` +
        `<div class="q-stmt">${esc(quizData.statement)}</div>` +
        `<div class="q-btns">` +
        `<button class="q-btn q-o" data-opt="O">⭕ 맞다</button>` +
        `<button class="q-btn q-x" data-opt="X">❌ 아니다</button>` +
        `</div>` +
        `<div class="q-result" hidden></div>`;
      root.appendChild(card);
      requestAnimationFrame(() => card.classList.add("show"));

      const btns = card.querySelectorAll(".q-btn");
      const resultEl = card.querySelector(".q-result");
      btns.forEach((btn) =>
        btn.addEventListener("click", async () => {
          const opt = btn.getAttribute("data-opt");
          btns.forEach((b) => (b.disabled = true));
          let result = null;
          try {
            result = await onAnswer(opt);
          } catch (e) {
            console.warn("[ALC] 퀴즈 채점 실패:", e);
          }
          resultEl.hidden = false;
          if (!result) {
            resultEl.textContent = "채점을 불러오지 못했어요. 잠시 후 다시 시도해요.";
            btns.forEach((b) => (b.disabled = false));
            return;
          }
          const ok = !!result.correct;
          card.classList.add(ok ? "correct" : "wrong");
          resultEl.innerHTML =
            `<strong>${ok ? "정답이에요! ✅ 다시 집중해서 읽어볼까요?" : "아쉬워요 ❌"}</strong>` +
            (result.explanation ? `<div class="q-exp">${esc(result.explanation)}</div>` : "");
          setTimeout(() => card.remove(), 6000);
        })
      );
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

    return { toast, badge, quiz, clear };
  }

  return { create };
})();
