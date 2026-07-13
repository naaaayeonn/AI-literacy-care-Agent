// Service Worker를 경유하는 fetch 프록시 함수 (CORS 및 CSP 블록 우회)
window.ALC_Fetch = async function (url, options = {}) {
  if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.sendMessage) {
    return fetch(url, options);
  }
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: "ALC_API_REQUEST", url, options }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      if (!response || !response.success) {
        reject(new Error(response ? response.error : "Unknown API error"));
        return;
      }
      resolve({
        ok: response.ok,
        status: response.status,
        statusText: response.statusText,
        json: async () => response.data,
      });
    });
  });
};

window.ALC_Session = (() => {
  function create({ cfg, userId, extract, getProgress, getReadChunkIndex, overlay, scrollTarget = window }) {
    const s = { id: null, queue: [], flushTimer: null, tracker: null, started: false };

    async function start() {
      if (s.started) return;
      s.started = true;

      const doc = extract();
      let data;
      try {
        // 서버 연결 시작 알림 (Render 무료 서버의 30초 대기 시간 대응)
        overlay.toast("⏳ AI 케어 서버에 연결하는 중...", "highlight");

        const res = await window.ALC_Fetch(`${cfg.API_BASE}/api/session/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userId,
            articleId: doc.url,
            source: { url: doc.url, title: doc.title, type: doc.type || "web" },
            content: doc.content,
          }),
        });
        data = await res.json();
      } catch (e) {
        console.warn("[ALC] 세션 시작 실패 (백엔드 미가동?):", e);
        overlay.toast("❌ AI 케어 서버 연결에 실패했습니다. 대시보드를 켜두었는지 확인해 주세요.", "nudge");
        s.started = false;
        return;
      }

      s.id = data.sessionId;
      // 디버그 모니터(다른 창)에 세션 연결 통보 — 창이 열려 있을 때만 반영.
      if (window.ALC_Debug) window.ALC_Debug.attachSession(s.id);
      s.tracker = ALC_Tracker.create({
        getProgress,
        getReadChunkIndex,
        onEvent: enqueue,
        scrollTarget,
        scrollThrottleMs: cfg.SCROLL_THROTTLE_MS,
        idleMs: cfg.IDLE_NUDGE_MS,
      });
      s.tracker.attach();
      s.flushTimer = setInterval(flush, cfg.FLUSH_INTERVAL_MS);
      console.log("[ALC] 세션 시작 - 세션 ID:", s.id, "유저 ID:", userId);
    }

    function enqueue(evt) {
      s.queue.push(evt);
      // 집중도 모니터에 원본 이벤트 실시간 전달(창이 열려 있을 때만).
      if (window.ALC_Debug) window.ALC_Debug.pushEvent(evt);
      // 중요 이벤트는 즉시 flush(개입 반응성 확보)
      if (evt.type === "blur" || evt.type === "pause") flush();
    }

    async function flush() {
      if (!s.id || s.queue.length === 0) return;
      const events = s.queue.splice(0, s.queue.length);
      try {
        const res = await window.ALC_Fetch(`${cfg.API_BASE}/api/session/${s.id}/events`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: s.id, events }),
        });
        render(await res.json());
      } catch (e) {
        const msg = e.message || String(e);
        if (msg.includes("message channel closed") || msg.includes("context invalidated")) {
          // 페이지 새로고침/창 닫기로 인한 정상적인 연결 끊김은 로그로만 처리
          console.log("[ALC] 페이지 이동/새로고침으로 통신 채널이 종료되었습니다.");
        } else {
          console.warn("[ALC] 이벤트 전송 실패:", e);
        }
      }
    }

    // 개입 명령(to_intervention_command) → 오버레이
    function render(cmd) {
      const p = (cmd && cmd.payload) || {};
      // 집중도 모니터에 서버 계산 결과(focusScore·감점 내역) 전달.
      if (window.ALC_Debug) window.ALC_Debug.pushResponse(cmd);
      // 집중도 배지는 개입 여부와 무관하게 응답마다 항상 갱신(모든 payload에 focusScore 포함).
      if (p.focusScore != null) overlay.badge(p.focusScore);
      switch (cmd && cmd.type) {
        case "nudge":
          overlay.toast(p.nudgeMessage || "잠시 멈추고 다시 읽어볼까요?", "nudge");
          break;
        case "highlight":
          overlay.toast(p.nudgeMessage || "핵심 문장에 집중해볼까요?", "highlight");
          break;
        case "quiz":
          // O/X 문항: quiz_data가 실려 오면 카드+버튼으로 띄우고 선택을 채점한다.
          // (측정 보장 트리거로 집중이 좋아도 뜰 수 있음). quiz 없으면 안내 토스트 폴백.
          if (p.quiz && p.quiz.quizId) {
            overlay.quiz(p.quiz, (selected) => submitQuiz(p.quiz.quizId, selected));
          } else {
            overlay.toast(p.nudgeMessage || "방금 읽은 내용을 퀴즈로 확인해보세요!", "quiz");
          }
          break;
        // score_update: 배지는 위에서 이미 갱신됨(별도 처리 불필요).
      }
    }

    // O/X 답안 채점 요청 → {correct, explanation, focusRecovered, xpEarned}.
    // overlay.quiz의 onAnswer 콜백으로 넘겨져 결과·해설 렌더에 쓰인다.
    async function submitQuiz(quizId, selectedOption) {
      if (!s.id) return null;
      const res = await window.ALC_Fetch(`${cfg.API_BASE}/api/session/${s.id}/quiz/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quizId, selectedOption }),
      });
      if (!res.ok) throw new Error(`quiz submit ${res.status}`);
      return await res.json();
    }

    async function stop() {
      if (!s.started) return;
      if (s.tracker) s.tracker.detach();
      if (s.flushTimer) clearInterval(s.flushTimer);
      await flush(); // 남은 이벤트 전송
      if (s.id) {
        // 세션 종료 → 최종 결과 계산(성장 그래프용). 대시보드 기록은 후속.
        try {
          await window.ALC_Fetch(`${cfg.API_BASE}/api/session/${s.id}/result`);
        } catch (_) {}
      }
      if (window.ALC_Debug) window.ALC_Debug.reset();
      overlay.clear();
      s.id = null;
      s.started = false;
      s.queue = [];
    }

    return { start, stop };
  }

  return { create };
})();
