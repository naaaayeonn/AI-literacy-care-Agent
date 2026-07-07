// 팝업: on/off 토글을 chrome.storage에 저장한다.
// content script가 storage.onChanged를 구독해 즉시 반응한다.

const checkbox = document.getElementById("enabled");
const label = document.getElementById("toggleLabel");
const status = document.getElementById("status");

function render(enabled) {
  checkbox.checked = enabled;
  label.textContent = enabled ? "켜짐" : "꺼짐";
  status.textContent = enabled ? "읽는 글을 모니터링하는 중…" : "";
}

(async () => {
  const { enabled = false } = await chrome.storage.local.get("enabled");
  render(enabled);
})();

checkbox.addEventListener("change", async () => {
  const enabled = checkbox.checked;
  await chrome.storage.local.set({ enabled });
  render(enabled);
});
