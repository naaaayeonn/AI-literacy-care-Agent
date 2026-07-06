const API_BASE = "http://localhost:8000/api";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "START_SESSION") {
    // 1. Get content from the active tab
    chrome.tabs.sendMessage(message.tabId, { type: "EXTRACT_CONTENT" }, async (contentResponse) => {
      const content = contentResponse ? contentResponse.content : [];
      const source = contentResponse ? contentResponse.source : { url: "unknown" };
      
      try {
        const res = await fetch(`${API_BASE}/session/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userId: "extension-user-001",
            content: content,
            source: source
          })
        });
        
        const data = await res.json();
        const sessionId = data.sessionId;
        
        // Save session
        chrome.storage.local.set({ sessionId: sessionId }, () => {
          // Tell content script to start tracking
          chrome.tabs.sendMessage(message.tabId, { type: "SESSION_STARTED", sessionId: sessionId });
          sendResponse({ success: true, sessionId: sessionId });
        });
      } catch (e) {
        console.error(e);
        sendResponse({ success: false, error: e.toString() });
      }
    });
    return true; // Keep message channel open for async
  }
  
  if (message.type === "STOP_SESSION") {
    chrome.storage.local.get(['sessionId'], async (res) => {
      if (!res.sessionId) {
        sendResponse({ success: false, error: "No active session" });
        return;
      }
      
      try {
        const finishRes = await fetch(`${API_BASE}/session/${res.sessionId}/finish`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            literacy_score: 0,
            comprehension_score: 0,
            engagement_score: 0
          }) // Dummy payload, backend will calculate
        });
        const finishData = await finishRes.json();
        
        // Fetch Result
        const resultRes = await fetch(`${API_BASE}/session/${res.sessionId}/result`);
        const resultData = await resultRes.json();
        
        // Clear session
        chrome.storage.local.remove('sessionId');
        
        // Tell all tabs to stop tracking
        chrome.tabs.query({}, (tabs) => {
          tabs.forEach(t => chrome.tabs.sendMessage(t.id, { type: "SESSION_STOPPED" }).catch(()=>{}));
        });
        
        sendResponse({ success: true, data: resultData });
      } catch (e) {
        console.error(e);
        sendResponse({ success: false, error: e.toString() });
      }
    });
    return true;
  }
  
  if (message.type === "FLUSH_EVENTS") {
    chrome.storage.local.get(['sessionId'], async (res) => {
      if (!res.sessionId) {
        sendResponse({ success: false });
        return;
      }
      
      try {
        const fetchRes = await fetch(`${API_BASE}/session/${res.sessionId}/events`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ events: message.events })
        });
        const data = await fetchRes.json();
        sendResponse({ success: true, intervention: data });
      } catch(e) {
        sendResponse({ success: false, error: e.toString() });
      }
    });
    return true;
  }
  
  if (message.type === "LOOKUP_TERM") {
    chrome.storage.local.get(['sessionId'], async (res) => {
      const sessionId = res.sessionId || "mock-session";
      try {
        const url = new URL(`${API_BASE}/terms/lookup`);
        url.searchParams.append("word", message.word);
        url.searchParams.append("sessionId", sessionId);
        
        const fetchRes = await fetch(url.toString());
        const data = await fetchRes.json();
        sendResponse({ success: true, term: data });
      } catch(e) {
        sendResponse({ success: false, error: e.toString() });
      }
    });
    return true;
  }
});
