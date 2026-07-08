const API_BASE = "http://localhost:8000/api";

// MV3 서비스 워커 async 메시지 처리 — chrome.storage callback 대신 Promise(await) 사용
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  if (message.type === "START_SESSION") {
    (async () => {
      try {
        const contentResponse = await chrome.tabs.sendMessage(message.tabId, { type: "EXTRACT_CONTENT" });
        const content = contentResponse ? contentResponse.content : [];
        const source = contentResponse ? contentResponse.source : { url: "unknown" };

        const res = await fetch(`${API_BASE}/session/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ userId: "extension-user-001", content, source })
        });
        const data = await res.json();
        const sessionId = data.sessionId;

        await chrome.storage.local.set({ sessionId });
        chrome.tabs.sendMessage(message.tabId, { type: "SESSION_STARTED", sessionId });
        sendResponse({ success: true, sessionId });
      } catch (e) {
        console.error("[BG] START_SESSION error:", e);
        sendResponse({ success: false, error: e.toString() });
      }
    })();
    return true;
  }

  if (message.type === "STOP_SESSION") {
    (async () => {
      try {
        const stored = await chrome.storage.local.get(['sessionId']);
        if (!stored.sessionId) {
          sendResponse({ success: false, error: "No active session" });
          return;
        }

        await fetch(`${API_BASE}/session/${stored.sessionId}/finish`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ literacy_score: 0, comprehension_score: 0, engagement_score: 0 })
        });

        const resultRes = await fetch(`${API_BASE}/session/${stored.sessionId}/result`);
        const resultData = await resultRes.json();

        await chrome.storage.local.remove('sessionId');

        const tabs = await chrome.tabs.query({});
        tabs.forEach(t => chrome.tabs.sendMessage(t.id, { type: "SESSION_STOPPED" }).catch(() => {}));

        sendResponse({ success: true, data: resultData });
      } catch (e) {
        console.error("[BG] STOP_SESSION error:", e);
        sendResponse({ success: false, error: e.toString() });
      }
    })();
    return true;
  }

  if (message.type === "FLUSH_EVENTS") {
    // fire-and-forget: 응답 채널 안 잡아서 "message channel closed" 에러 방지
    (async () => {
      try {
        const stored = await chrome.storage.local.get(['sessionId']);
        if (!stored.sessionId) return;

        const fetchRes = await fetch(`${API_BASE}/session/${stored.sessionId}/events`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ events: message.events })
        });
        const data = await fetchRes.json();

        // 개입(intervention)이 있으면 탭으로 직접 전송
        if (data && data.payload && sender.tab && sender.tab.id) {
          chrome.tabs.sendMessage(sender.tab.id, {
            type: "INTERVENTION",
            intervention: data
          }).catch(() => {});
        }
      } catch (e) {
        console.error("[BG] FLUSH_EVENTS error:", e);
      }
    })();
    // return true 안 함 → 채널 즉시 닫힘, 에러 없음
    return;
  }

  if (message.type === "LOOKUP_TERM") {
    (async () => {
      try {
        const stored = await chrome.storage.local.get(['sessionId']);
        const sessionId = stored.sessionId || "mock-session";

        const fetchRes = await fetch(`${API_BASE}/terms/lookup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            word: message.word,
            sessionId,
            context: message.context || null,
          })
        });
        const data = await fetchRes.json();
        sendResponse({ success: true, term: data });
      } catch (e) {
        console.error("[BG] LOOKUP_TERM error:", e);
        sendResponse({ success: false, error: e.toString() });
      }
    })();
    return true;
  }
});
