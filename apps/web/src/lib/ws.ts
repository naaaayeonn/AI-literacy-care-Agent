/**
 * ④→③ WebSocket 클라이언트 stub (6/21 타입 확정)
 * ③번 백엔드는 이 파일의 이벤트 스키마를 참고해 수신/송신 로직을 구현한다.
 */
import type { ReadingBehaviorEvent, InterventionCommand } from './api';

export type MessageHandler = (command: InterventionCommand) => void;

interface WsClient {
  send: (event: ReadingBehaviorEvent) => void;
  onMessage: (handler: MessageHandler) => void;
  close: () => void;
  isConnected: () => boolean;
}

/**
 * WebSocket 클라이언트 생성
 * TODO 7/6: 실제 WebSocket 연결 구현
 */
export const createWsClient = (endpoint: string): WsClient => {
  console.log(`[WS] Connecting to: ${endpoint}`);
  // TODO 7/6: 실제 WebSocket 구현 시 아래 주석 해제
  // const ws = new WebSocket(endpoint);
  // let _connected = false;
  // ws.onopen = () => { _connected = true; };
  // ws.onmessage = (e) => { messageHandler?.(JSON.parse(e.data)); };
  // ws.onclose = () => { _connected = false; };

  let messageHandler: MessageHandler | null = null;

  return {
    send: (event: ReadingBehaviorEvent) => {
      console.log('[WS] → Server:', event);
      // TODO 7/6: ws.send(JSON.stringify(event));
    },
    onMessage: (handler: MessageHandler) => {
      messageHandler = handler;
      // TODO 7/6: ws.onmessage = (e) => messageHandler?.(JSON.parse(e.data));
      void messageHandler; // 실제 ws 연결 전까지 참조 유지
      console.log('[WS] Message handler registered');
    },
    close: () => {
      messageHandler = null;
      console.log('[WS] Connection closed');
    },
    isConnected: () => false,  // TODO 7/6: ws.readyState === WebSocket.OPEN
  };
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
