document.addEventListener('DOMContentLoaded', () => {
  const btnStart = document.getElementById('btn-start');
  const btnStop = document.getElementById('btn-stop');
  const statusText = document.getElementById('status-text');
  const resultBox = document.getElementById('result-box');
  const scoreVal = document.getElementById('score-val');
  const messageVal = document.getElementById('message-val');

  // Check current status
  chrome.storage.local.get(['sessionId'], (res) => {
    if (res.sessionId) {
      setSessionActive(true);
    } else {
      setSessionActive(false);
    }
  });

  function setSessionActive(isActive) {
    if (isActive) {
      btnStart.disabled = true;
      btnStop.disabled = false;
      statusText.textContent = "현재 페이지를 분석 및 케어 중입니다...";
      resultBox.classList.add('hidden');
    } else {
      btnStart.disabled = false;
      btnStop.disabled = true;
      statusText.textContent = "대기 중...";
    }
  }

  btnStart.addEventListener('click', () => {
    // Tell background to start session for active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0].id;
      chrome.runtime.sendMessage({ type: "START_SESSION", tabId: tabId }, (response) => {
        if (response && response.success) {
          setSessionActive(true);
        } else {
          statusText.textContent = "오류: 서버 연결 실패";
        }
      });
    });
  });

  btnStop.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: "STOP_SESSION" }, (response) => {
      setSessionActive(false);
      if (response && response.data) {
        resultBox.classList.remove('hidden');
        scoreVal.textContent = response.data.engagement_score || 0;
        messageVal.textContent = response.data.message || "세션 종료됨";
      }
    });
  });
});
