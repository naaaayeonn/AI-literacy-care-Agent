// MV3 service worker — 상태 기본값 + PDF 링크 가로채기(declarativeNetRequest).
// (실제 측정·개입은 content script(웹)와 pdf/viewer.js(PDF)가 페이지에서 수행한다.)

const DEFAULT_STATE = { enabled: false };
const PDF_RULE_ID = 1;

// enabled일 때만 PDF 링크(main_frame)를 우리 pdf.js 뷰어로 리다이렉트한다.
// 원본 URL(\\0=매치 전체)을 ?file= 뒤에 실어 넘긴다(viewer.js가 split으로 복원).
// file:// 로컬 PDF는 규칙 대상이 아니라 팝업의 "문서 열기"(파일 피커)로 처리한다.
async function setPdfRedirect(enabled) {
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
}

chrome.runtime.onInstalled.addListener(async () => {
  const cur = await chrome.storage.local.get("enabled");
  if (cur.enabled === undefined) await chrome.storage.local.set(DEFAULT_STATE);
  await setPdfRedirect(!!cur.enabled);
});

chrome.runtime.onStartup.addListener(async () => {
  const { enabled = false } = await chrome.storage.local.get("enabled");
  await setPdfRedirect(!!enabled);
});

// 토글 시: PDF 리다이렉트 규칙 갱신 + 디버깅 로그.
// (content script는 storage.onChanged를 직접 구독하므로 별도 중계 불필요.)
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local" || !changes.enabled) return;
  console.log("[ALC] enabled:", changes.enabled.newValue);
  setPdfRedirect(!!changes.enabled.newValue);
});
