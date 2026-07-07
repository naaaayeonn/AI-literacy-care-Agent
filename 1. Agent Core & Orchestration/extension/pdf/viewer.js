// AI 리터러시 케어 — PDF 뷰어 (pdf.js). EXTENSION_DESIGN §9.
//
// PDF를 pdf.js로 "일반 DOM"으로 되돌려, 웹페이지와 동일한 shared 모듈
// (tracker/overlay/session_client)을 그대로 재사용한다. 이 파일은 PDF용
// extract()/getProgress()만 주입하는 "PDF 어댑터"다.
//
// 진입 2경로:
//   1) ?file=<원본URL>  — service_worker의 declarativeNetRequest가 PDF 링크를 가로채 리다이렉트
//   2) 파일 피커        — 로컬 PDF를 열기(서버 업로드 없음, ADR-002)

import * as pdfjsLib from "../vendor/pdfjs/pdf.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL(
  "vendor/pdfjs/pdf.worker.mjs"
);

const CFG = window.ALC_CONFIG;
const overlay = window.ALC_Overlay.create();

const viewerEl = document.getElementById("viewer");
const emptyEl = document.getElementById("empty");
const titleEl = document.getElementById("doc-title");
const progressEl = document.getElementById("progress-label");
const fileInput = document.getElementById("file-input");

let extractedContent = []; // 백엔드로 보낼 content[]
let session = null;

// ── shared에 주입할 PDF 어댑터 ─────────────────────────
// 진행률: 뷰어 스크롤 컨테이너 기준(0~1)
function getProgress() {
  const max = viewerEl.scrollHeight - viewerEl.clientHeight;
  return max > 0 ? viewerEl.scrollTop / max : 0;
}

// 본문: 이미 추출해 둔 content[]를 그대로 반환
function extract() {
  return {
    title: document.title,
    url: location.href,
    type: "pdf",
    content: extractedContent,
  };
}

// 설치별 익명 UUID (ADR-002)
async function getUserId() {
  const { userId } = await chrome.storage.local.get("userId");
  if (userId) return userId;
  const id =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : "u_" + Date.now() + "_" + Math.floor(Math.random() * 1e6);
  await chrome.storage.local.set({ userId: id });
  return id;
}

// ── pdf.js 텍스트 아이템 → 문단 재구성 ──────────────────
// y좌표로 줄 분리, 빈 줄로 문단 분리, 하이픈 줄바꿈(`-`) 병합.
function itemsToParagraphs(textContent) {
  const lines = [];
  let cur = "";
  let lastY = null;
  for (const item of textContent.items) {
    const y = item.transform ? item.transform[5] : lastY;
    if (lastY !== null && Math.abs(y - lastY) > 3) {
      lines.push(cur.trim());
      cur = "";
    }
    cur += item.str || "";
    if (item.hasEOL) {
      lines.push(cur.trim());
      cur = "";
    }
    lastY = y;
  }
  if (cur.trim()) lines.push(cur.trim());

  const paras = [];
  let buf = "";
  for (const ln of lines) {
    if (!ln) {
      if (buf.trim()) {
        paras.push(buf.trim());
        buf = "";
      }
      continue;
    }
    if (buf.endsWith("-")) buf = buf.slice(0, -1) + ln;
    else buf += (buf ? " " : "") + ln;
  }
  if (buf.trim()) paras.push(buf.trim());
  return paras.filter((p) => p.length > 0);
}

// ── 렌더 ───────────────────────────────────────────────
async function renderPdf(source) {
  viewerEl.innerHTML = "";
  extractedContent = [];
  const pdf = await pdfjsLib.getDocument(source).promise;
  const allParas = [];

  for (let n = 1; n <= pdf.numPages; n++) {
    const page = await pdf.getPage(n);
    const viewport = page.getViewport({ scale: 1.4 });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    viewerEl.appendChild(canvas);
    await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;

    const text = await page.getTextContent();
    allParas.push(...itemsToParagraphs(text));
    progressEl.textContent = `${n}/${pdf.numPages}쪽`;
  }

  extractedContent = allParas.length
    ? allParas
    : ["(빈 문서 또는 스캔 PDF — 텍스트 레이어 없음. OCR은 후속.)"];
  emptyEl.classList.add("hidden");
  await startSessionIfEnabled();
}

async function startSessionIfEnabled() {
  const { enabled = false } = await chrome.storage.local.get("enabled");
  if (!enabled || session || extractedContent.length === 0) return;
  const userId = await getUserId();
  session = window.ALC_Session.create({
    cfg: CFG,
    userId,
    extract,
    getProgress,
    overlay,
    scrollTarget: viewerEl,
  });
  session.start();
}

// ── 진입 처리 ──────────────────────────────────────────
// ?file= 뒤 전체를 원본 URL로 취급(원본에 ? 포함 가능 → split 사용, 파싱 X)
function fileParamFromUrl() {
  const marker = "?file=";
  const i = location.href.indexOf(marker);
  if (i === -1) return null;
  try {
    return decodeURIComponent(location.href.slice(i + marker.length));
  } catch (_) {
    return location.href.slice(i + marker.length);
  }
}

fileInput.addEventListener("change", async () => {
  const file = fileInput.files && fileInput.files[0];
  if (!file) return;
  titleEl.textContent = file.name;
  document.title = file.name;
  if (session) {
    session.stop();
    session = null;
  }
  const buf = await file.arrayBuffer();
  renderPdf({ data: new Uint8Array(buf) });
});

window.addEventListener("pagehide", () => {
  if (session) session.stop();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local" || !changes.enabled) return;
  if (changes.enabled.newValue) startSessionIfEnabled();
  else if (session) {
    session.stop();
    session = null;
  }
});

(async () => {
  const src = fileParamFromUrl();
  if (src) {
    titleEl.textContent = src.split("/").pop() || "PDF";
    document.title = titleEl.textContent;
    // pdf.js가 원본 URL을 fetch (host_permissions <all_urls>)
    renderPdf(src);
  }
})();
