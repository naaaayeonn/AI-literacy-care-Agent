let isSessionActive = false;
let eventsQueue = [];
let lastScrollY = window.scrollY;
let lastInteractionTime = Date.now();

// 1. Text Extraction
function extractContent() {
  const paragraphs = Array.from(document.querySelectorAll('p, h1, h2, h3, article, section'))
                          .map(el => el.innerText.trim())
                          .filter(text => text.length > 20);
  return {
    content: paragraphs,
    source: { url: window.location.href, title: document.title }
  };
}

// 2. Event Tracking
function trackEvent(type, payload = {}) {
  if (!isSessionActive) return;
  eventsQueue.push({
    type: type,
    timestamp_ms: Date.now(),
    position: payload.position || window.scrollY,
    duration_ms: payload.durationMs || 1000
  });
  
  if (eventsQueue.length >= 5) {
    flushEvents();
  }
}

function flushEvents() {
  if (eventsQueue.length === 0) return;
  
  const toSend = [...eventsQueue];
  eventsQueue = [];
  
  chrome.runtime.sendMessage({ type: "FLUSH_EVENTS", events: toSend }, (res) => {
    if (res && res.intervention && res.intervention.payload) {
      handleIntervention(res.intervention);
    }
  });
}

function handleIntervention(command) {
  if (command.type === 'nudge') {
    // Show a subtle nudge notification
    const nudge = document.createElement('div');
    nudge.style.cssText = "position:fixed; top:20px; right:20px; background:#fef08a; color:#854d0e; padding:12px; border-radius:8px; z-index:999999; box-shadow:0 4px 6px rgba(0,0,0,0.1); font-weight:bold;";
    nudge.textContent = `💡 ${command.payload.nudgeMessage || "집중력이 떨어지고 있어요! 다시 읽어볼까요?"}`;
    document.body.appendChild(nudge);
    setTimeout(() => nudge.remove(), 5000);
  }
}

// 3. Setup Listeners
window.addEventListener('scroll', () => {
  if (!isSessionActive) return;
  const currentScrollY = window.scrollY;
  const delta = Math.abs(currentScrollY - lastScrollY);
  if (delta > 300) {
    // Fast scroll detection
    trackEvent('scroll', { durationMs: 200, position: currentScrollY });
    lastScrollY = currentScrollY;
  }
});

window.addEventListener('visibilitychange', () => {
  if (!isSessionActive) return;
  if (document.visibilityState === 'hidden') {
    trackEvent('blur', { durationMs: 0 }); // Will calculate duration on backend or next focus
  } else {
    trackEvent('focus');
  }
});

// Periodic dwell check
setInterval(() => {
  if (isSessionActive && document.visibilityState === 'visible') {
    trackEvent('dwell', { durationMs: 2000 });
    flushEvents();
  }
}, 2000);

// 4. RAG Term Lookup (Hover/Double Click/Drag)
function handleTextSelection(e) {
  // 세션 없어도 단어 조회는 허용 (케어 시작 전에도 동작)
  
  // Ignore clicks inside the tooltip
  if (currentTooltip && currentTooltip.contains(e.target)) return;
  
  // Use setTimeout to allow the browser to complete the selection process
  setTimeout(() => {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();
    
    if (selectedText.length > 0 && selectedText.length < 30) {
      console.log("AI Literacy Care - Text selected:", selectedText);
      
      // 1번 RAG 팀 context 필드: 드래그한 단어 주변 문장을 추출해서 함께 전송 (LLM 동음이의어 구분 정확도 향상)
      let context = null;
      try {
        const anchorNode = selection.anchorNode;
        if (anchorNode && anchorNode.textContent) {
          // 해당 텍스트 노드의 전체 텍스트에서 선택된 단어가 속한 문장을 추출
          const fullText = anchorNode.textContent;
          // 단어 위치 찾기
          const wordIndex = fullText.indexOf(selectedText);
          if (wordIndex !== -1) {
            // 앞뒤 100자 정도를 context로 활용
            const start = Math.max(0, wordIndex - 60);
            const end = Math.min(fullText.length, wordIndex + selectedText.length + 60);
            context = fullText.slice(start, end).trim();
          }
        }
      } catch (e) {
        // context 추출 실패 시 조용히 무시
      }
      
      // Lookup term
      chrome.runtime.sendMessage({ type: "LOOKUP_TERM", word: selectedText, context }, (res) => {
        if (res && res.success && res.term && res.term.source !== 'not_found' && res.term.definition) {
          showTooltip(e.pageX, e.pageY, res.term);
        }
        // source가 not_found이면 툴팁을 아예 표시하지 않음 (조용히 무시)
      });
    }
  }, 50);
}

document.addEventListener('mouseup', handleTextSelection);
document.addEventListener('dblclick', handleTextSelection);

let currentTooltip = null;

function showTooltip(x, y, termData) {
  if (currentTooltip) {
    currentTooltip.remove();
  }
  
  const tooltip = document.createElement('div');
  tooltip.className = 'rag-tooltip';
  tooltip.style.left = `${x + 10}px`;
  tooltip.style.top = `${y + 10}px`;
  
  tooltip.innerHTML = `
    <span class="rag-tooltip-close">×</span>
    <h4>${termData.term}</h4>
    <p>${termData.definition}</p>
    ${termData.source ? `<p class="source">[출처] ${termData.source}</p>` : ''}
  `;
  
  tooltip.querySelector('.rag-tooltip-close').addEventListener('click', () => {
    tooltip.remove();
    currentTooltip = null;
  });
  
  document.body.appendChild(tooltip);
  currentTooltip = tooltip;
}

// Remove tooltip on outside click
document.addEventListener('click', (e) => {
  if (currentTooltip && !currentTooltip.contains(e.target)) {
    currentTooltip.remove();
    currentTooltip = null;
  }
});

// 5. Message Handling
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "EXTRACT_CONTENT") {
    sendResponse(extractContent());
  } else if (message.type === "SESSION_STARTED") {
    isSessionActive = true;
    eventsQueue = [];
    console.log("AI Literacy Care: Session Started");
  } else if (message.type === "SESSION_STOPPED") {
    isSessionActive = false;
    flushEvents();
    console.log("AI Literacy Care: Session Stopped");
  }
  return true;
});

// Check if already active on load
chrome.storage.local.get(['sessionId'], (res) => {
  if (res.sessionId) {
    isSessionActive = true;
  }
});
