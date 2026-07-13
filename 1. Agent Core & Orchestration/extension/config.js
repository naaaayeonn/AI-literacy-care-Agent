// 확장 전역 설정. content script·popup·pdf 뷰어가 함께 참조한다.
// 백엔드 주소가 바뀌면 여기만 고치면 된다.
window.ALC_CONFIG = {
  // 127.0.0.1(IPv4 리터럴)로 고정 — Windows Chrome은 localhost를 IPv6(::1)로
  // 먼저 해석하는데 백엔드가 IPv4에만 뜨면 "Failed to fetch"가 난다. IP 리터럴은
  // DNS 해석을 건너뛰어 어느 OS에서든 결정적으로 IPv4 서버에 붙는다.
  API_BASE: "https://ai-literacy-backend.onrender.com",
  // 전송은 REST(ADR-001). WebSocket 없음.

  // 읽기 세션 자동 시작 임계값
  MIN_READABLE_CHARS: 800, // 본문이 이 글자 수 이상이면 "읽을 만한 글"로 판정
  START_DWELL_MS: 3000, // 페이지에 이만큼 머무르면 세션 시작
  SCROLL_THROTTLE_MS: 120, // 스크롤 이벤트 캡처 최소 간격

  // REST 전송(ADR-001)
  FLUSH_INTERVAL_MS: 1500, // 이벤트 큐를 이 주기로 배치 전송(blur/pause는 즉시)
  IDLE_NUDGE_MS: 20000, // 무동작 이만큼 지속되면 pause 이벤트 → 서버가 넛지 응답

  // 사용자 식별은 설치별 익명 UUID(ADR-002) — chrome.storage.local.userId.
  // 로그인 없음. content script가 없으면 생성한다.
};
