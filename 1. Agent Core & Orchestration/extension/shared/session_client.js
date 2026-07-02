// 공용 세션/전송 글루 (웹 · PDF 뷰어 공용) — window.ALC_Session
//
// tracker(이벤트) + overlay(개입 UI) + REST 전송(ADR-001)을 묶는다.
// 본문추출(extract)과 진행률(getProgress)만 주입하면 웹·PDF가 동일하게 동작한다.
//   - 웹:  extract=<p>/Readability, getProgress=scrollY/max, scrollTarget=window
//   - PDF: extract=pdf.js getTextContent, getProgress=page/total, scrollTarget=뷰어 컨테이너
//
// 전송: 이벤트를 큐에 모아 FLUSH_INTERVAL_MS마다(또는 blur/pause 즉시) POST /events →
//       응답의 개입 명령을 overlay로 렌더. 고정주기 폴링 아님(이벤트 구동).
window.ALC_Session = (() => {
  function create({ cfg, userId, extract, getProgress, overlay, scrollTarget = window }) {
    const s = { id: null, queue: [], flushTimer: null, tracker: null, started: false };

    async function start() {
      if (s.started) return;
      s.started = true;

      const doc = extract();
      let data;
      try {
        const res = await fetch(`${cfg.API_BASE}/api/session/start`, {
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
        s.started = false;
        return;
      }

      s.id = data.sessionId;
      s.tracker = ALC_Tracker.create({
        getProgress,
        onEvent: enqueue,
        scrollTarget,
        scrollThrottleMs: cfg.SCROLL_THROTTLE_MS,
        idleMs: cfg.IDLE_NUDGE_MS,
      });
      s.tracker.attach();
      s.flushTimer = setInterval(flush, cfg.FLUSH_INTERVAL_MS);
      console.log("[ALC] 세션 시작:", s.id);
    }

    function enqueue(evt) {
      s.queue.push(evt);
      // 중요 이벤트는 즉시 flush(개입 반응성 확보)
      if (evt.type === "blur" || evt.type === "pause") flush();
    }

    async function flush() {
      if (!s.id || s.queue.length === 0) return;
      const events = s.queue.splice(0, s.queue.length);
      try {
        const res = await fetch(`${cfg.API_BASE}/api/session/${s.id}/events`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: s.id, events }),
        });
        render(await res.json());
      } catch (e) {
        console.warn("[ALC] 이벤트 전송 실패:", e);
      }
    }

    // 개입 명령(to_intervention_command) → 오버레이
    function render(cmd) {
      const p = (cmd && cmd.payload) || {};
      switch (cmd && cmd.type) {
        case "nudge":
          overlay.toast(p.nudgeMessage || "잠시 멈추고 다시 읽어볼까요?", "nudge");
          break;
        case "highlight":
          overlay.toast(p.nudgeMessage || "핵심 문장에 집중해볼까요?", "highlight");
          break;
        case "quiz":
          overlay.toast(p.nudgeMessage || "방금 읽은 내용을 퀴즈로 확인해보세요!", "quiz");
          break;
        case "score_update":
          overlay.badge(p.focusScore);
          break;
      }
    }

    async function stop() {
      if (!s.started) return;
      if (s.tracker) s.tracker.detach();
      if (s.flushTimer) clearInterval(s.flushTimer);
      await flush(); // 남은 이벤트 전송
      if (s.id) {
        // 세션 종료 → 최종 결과 계산(성장 그래프용). 대시보드 기록은 후속.
        try {
          await fetch(`${cfg.API_BASE}/api/session/${s.id}/result`);
        } catch (_) {}
      }
      overlay.clear();
      s.id = null;
      s.started = false;
      s.queue = [];
    }

    return { start, stop };
  }

  return { create };
})();
