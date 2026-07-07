/**
 * ④→③ WebSocket 클라이언트 (7/6 실구현 완료)
 * 브라우저 Native WebSocket API를 사용해 백엔드 서버와 연결하고,
 * 사용자의 실시간 읽기 행동 이벤트를 송신하며 서버의 개입 명령을 수신합니다.
 */
import type { ReadingBehaviorEvent, InterventionCommand } from './api';

export type MessageHandler = (command: InterventionCommand) => void;

export interface WsClient {
  send: (event: ReadingBehaviorEvent) => void;
  onMessage: (handler: MessageHandler) => void;
  close: () => void;
  isConnected: () => boolean;
}

// 싱글톤 형태의 활성 클라이언트 참조 관리 (순환 참조 방지 및 전역 접근 용이성 확보)
let activeClient: WsClient | null = null;

export const getActiveWsClient = (): WsClient | null => activeClient;
export const setActiveWsClient = (client: WsClient | null) => {
  activeClient = client;
};

/**
 * WebSocket 클라이언트 생성 및 실제 소켓 연결 수립
 */
export const createWsClient = (endpoint: string): WsClient => {
  console.log(`[WS] Connecting to: ${endpoint}`);
  
  const ws = new WebSocket(endpoint);
  let messageHandler: MessageHandler | null = null;

  ws.onopen = () => {
    console.log('[WS] Connected successfully');
  };

  ws.onmessage = (e) => {
    try {
      const command = JSON.parse(e.data);
      console.log('[WS] ← Received Command:', command);
      messageHandler?.(command);
    } catch (err) {
      console.error('[WS] Failed to parse incoming server message:', err);
    }
  };

  ws.onclose = (e) => {
    console.log('[WS] Connection closed:', e.reason);
  };

  ws.onerror = (err) => {
    console.error('[WS] WebSocket error detected:', err);
  };

  const client: WsClient = {
    send: (event: ReadingBehaviorEvent) => {
      console.log('[WS] → Send Behavior Event:', event);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(event));
      } else {
        console.warn('[WS] Cannot send event. WebSocket state is not OPEN');
      }
    },
    onMessage: (handler: MessageHandler) => {
      messageHandler = handler;
      console.log('[WS] Registered message handler');
    },
    close: () => {
      messageHandler = null;
      ws.close();
      console.log('[WS] Closed manually');
    },
    isConnected: () => ws.readyState === WebSocket.OPEN,
  };

  // 활성 클라이언트로 지정
  setActiveWsClient(client);

  return client;
};

/** 읽기 행동 이벤트 전송 헬퍼 */
export const sendScrollEvent = (
  client: WsClient,
  sessionId: string,
  scrollVelocity: number,
  progress: number
) => {
  client.send({
    type: 'scroll',
    sessionId,
    timestamp: Date.now(),
    payload: { scrollVelocity, progress },
  });
};

export const sendDwellEvent = (
  client: WsClient,
  sessionId: string,
  paragraphId: string,
  dwellMs: number
) => {
  client.send({
    type: 'dwell',
    sessionId,
    timestamp: Date.now(),
    payload: { paragraphId, dwellMs },
  });
};

export const sendBlurEvent = (client: WsClient, sessionId: string) => {
  client.send({ type: 'blur', sessionId, timestamp: Date.now(), payload: {} });
};

export const sendFocusEvent = (client: WsClient, sessionId: string) => {
  client.send({ type: 'focus', sessionId, timestamp: Date.now(), payload: {} });
};
