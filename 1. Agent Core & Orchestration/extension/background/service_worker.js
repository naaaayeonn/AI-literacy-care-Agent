// MV3 service worker — 상태 기본값 + PDF 링크 가로채기(declarativeNetRequest).
// (실제 측정·개입은 content script(웹)와 pdf/viewer.js(PDF)가 페이지에서 수행한다.)

const DEFAULT_STATE = { enabled: true };
const PDF_RULE_ID = 1;

// enabled일 때만 PDF 링크(main_frame)를 우리 pdf.js 뷰어로 리다이렉트한다.
// 원본 URL(\\0=매치 전체)을 ?file= 뒤에 실어 넘긴다(viewer.js가 split으로 복원).
// file:// 로컬 PDF는 규칙 대상이 아니라 팝업의 "문서 열기"(파일 피커)로 처리한다.
async function setPdfRedirect(enabled) {
  try {
    const viewer = chrome.runtime.getURL("pdf/viewer.html");
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: [PDF_RULE_ID],
      addRules: enabled
        ? [
            {
              id: PDF_RULE_ID,
              priority: 1,
              action: {
                type: "redirect",
                redirect: { regexSubstitution: viewer + "?file=\\0" },
              },
              condition: {
                regexFilter: "^https?://.*\\.pdf($|\\?)",
                resourceTypes: ["main_frame"],
              },
            },
          ]
        : [],
    });
  } catch (e) {
    console.error("[ALC Background] setPdfRedirect failed:", e);
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  try {
    const cur = await chrome.storage.local.get("enabled");
    if (cur.enabled === undefined) await chrome.storage.local.set(DEFAULT_STATE);
    await setPdfRedirect(!!cur.enabled);
  } catch (e) {
    console.error("[ALC Background] onInstalled failed:", e);
  }
});

chrome.runtime.onStartup.addListener(async () => {
  try {
    const { enabled = false } = await chrome.storage.local.get("enabled");
    await setPdfRedirect(!!enabled);
  } catch (e) {
    console.error("[ALC Background] onStartup failed:", e);
  }
});

// 토글 시: PDF 리다이렉트 규칙 갱신 + 디버깅 로그.
// (content script는 storage.onChanged를 직접 구독하므로 별도 중계 불필요.)
chrome.storage.onChanged.addListener((changes, area) => {
  try {
    if (area !== "local" || !changes.enabled) return;
    console.log("[ALC] enabled:", changes.enabled.newValue);
    setPdfRedirect(!!changes.enabled.newValue);
  } catch (e) {
    console.error("[ALC Background] storage onChanged failed:", e);
  }
});

// 백엔드 API 요청 프록시 (CORS / CSP 차단 우회용 + 자동 재시도 + 포트 기반 영구 채널 유지)
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "ALC_PORT") {
    port.onMessage.addListener(async (message) => {
      if (message.type === "ALC_API_REQUEST") {
        const { requestId, url, options } = message;
        
        // 최대 3회 재시도 (Render 콜드 스타트 및 일시적 오류 대응)
        const executeFetchWithRetry = async (retriesLeft, delay) => {
          try {
            const res = await fetch(url, options);
            const ok = res.ok;
            const status = res.status;
            const statusText = res.statusText;
            let data = null;
            try {
              data = await res.json();
            } catch (_) {}
            
            // 포트가 아직 열려있는지 안전 확인 후 응답 전송
            try {
              port.postMessage({ success: true, requestId, ok, status, statusText, data });
            } catch (e) {
              console.warn("[ALC Background] Failed to send response back through port:", e);
            }
          } catch (err) {
            if (retriesLeft > 0) {
              console.warn(`[ALC Background] Fetch failed, retrying in ${delay}ms... (${retriesLeft} retries left):`, err);
              setTimeout(() => executeFetchWithRetry(retriesLeft - 1, delay * 2), delay);
            } else {
              console.error("[ALC Background] Promise fetch failed after all retries:", err);
              try {
                port.postMessage({ success: false, requestId, error: err.toString() });
              } catch (e) {}
            }
          }
        };

        executeFetchWithRetry(3, 1000);
      }
    });
  }
});
