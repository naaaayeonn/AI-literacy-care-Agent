/**
 * sessionConfigStore — 온보딩/모드/업로드 세션 설정
 * 링크 배포용 흐름: 익명 로그인(UUID) → 개인정보 동의 → 모드 선택(care/upload)
 * userId·동의 여부는 localStorage에 영구 저장하여 재방문 시 유지한다.
 */
import { create } from 'zustand';

const UID_KEY = 'literacy_uid';
const CONSENT_KEY = 'literacy_consent';
const BASELINE_KEY = 'literacy_baseline';
const UPLOAD_KEY = 'literacy_upload';

function loadUserId(): string | null {
  try {
    return localStorage.getItem(UID_KEY);
  } catch {
    return null;
  }
}

/** 온보딩 캘리브레이션에서 측정한 개인별 기준 스크롤 속도 로드 */
function loadBaseline(): { easy: number; hard: number; dEasy?: number; dHard?: number } | null {
  try {
    const raw = localStorage.getItem(BASELINE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (typeof parsed.easy === 'number' && typeof parsed.hard === 'number') {
        return parsed;
      }
    }
  } catch {
    /* noop */
  }
  return null;
}

function loadConsent(): boolean {
  try {
    return localStorage.getItem(CONSENT_KEY) === 'true';
  } catch {
    return false;
  }
}

/** 새로고침 후에도 "지금 읽던 업로드 문서"를 복원하기 위해 localStorage에서 로드 */
function loadUpload(): { title: string | null; content: string[] | null; mode: 'care' | 'upload' } {
  try {
    const raw = localStorage.getItem(UPLOAD_KEY);
    if (raw) {
      const p = JSON.parse(raw);
      if (Array.isArray(p.content) && p.content.length > 0) {
        return { title: p.title ?? null, content: p.content, mode: 'upload' };
      }
    }
  } catch {
    /* noop */
  }
  return { title: null, content: null, mode: 'care' };
}

function genUserId(): string {
  const raw =
    (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function'
      ? globalThis.crypto.randomUUID()
      : String(Math.random()).slice(2) + String(Math.random()).slice(2)).replace(/-/g, '');
  return 'u_anon_' + raw.slice(0, 12);
}

export type CareMode = 'care' | 'upload';

interface SessionConfigState {
  userId: string | null;
  consentGiven: boolean;
  mode: CareMode;
  uploadedTitle: string | null;
  uploadedContent: string[] | null; // 단락 배열

  /** 온보딩 캘리브레이션 — 개인별 기준 스크롤 속도 (px/ms) */
  baselineScrollSpeed: { easy: number; hard: number; dEasy?: number; dHard?: number } | null;
  /** 캘리브레이션 완료 여부 */
  isCalibrated: boolean;

  /** 익명 UUID 발급(최초 1회) + 동의 저장. 발급된 userId 반환 */
  onboard: () => string;
  /** 캘리브레이션 결과 저장 */
  setBaseline: (easy: number, hard: number) => void;
  setMode: (m: CareMode) => void;
  setUpload: (title: string, content: string[]) => void;
  clearUpload: () => void;
  reset: () => void;
}

const _initUpload = loadUpload();

export const useSessionConfig = create<SessionConfigState>((set, get) => ({
  userId: loadUserId(),
  consentGiven: loadConsent(),
  mode: _initUpload.mode,
  uploadedTitle: _initUpload.title,
  uploadedContent: _initUpload.content,
  baselineScrollSpeed: loadBaseline(),
  isCalibrated: loadBaseline() !== null,

  onboard: () => {
    let uid = get().userId;
    if (!uid) {
      uid = genUserId();
      try {
        localStorage.setItem(UID_KEY, uid);
      } catch {
        /* localStorage 불가 환경 무시 */
      }
    }
    try {
      localStorage.setItem(CONSENT_KEY, 'true');
    } catch {
      /* noop */
    }
    set({ userId: uid, consentGiven: true });
    return uid;
  },

  setMode: (mode) => set({ mode }),
  setUpload: (uploadedTitle, uploadedContent) => {
    // 새로고침 후 복원용으로 업로드 문서를 localStorage에 저장한다.
    try {
      localStorage.setItem(UPLOAD_KEY, JSON.stringify({ title: uploadedTitle, content: uploadedContent }));
    } catch {
      /* noop */
    }
    set({ mode: 'upload', uploadedTitle, uploadedContent });
  },
  clearUpload: () => {
    try {
      localStorage.removeItem(UPLOAD_KEY);
    } catch {
      /* noop */
    }
    set({ mode: 'care', uploadedTitle: null, uploadedContent: null });
  },

  setBaseline: (easy, hard) => {
    // 온보딩 쉬운/어려운 지문의 난이도(2번 척도). 지문이 고정이라 대표값으로 둔다.
    // 백엔드가 이 dEasy/dHard로 "난이도별 개인 읽기 속도 직선"을 세운다.
    const baseline = {
      easy: parseFloat(easy.toFixed(3)),
      hard: parseFloat(hard.toFixed(3)),
      dEasy: 20,
      dHard: 75,
    };
    try {
      localStorage.setItem(BASELINE_KEY, JSON.stringify(baseline));
    } catch {
      /* noop */
    }
    set({ baselineScrollSpeed: baseline, isCalibrated: true });
  },

  reset: () => {
    try {
      localStorage.removeItem(UID_KEY);
      localStorage.removeItem(CONSENT_KEY);
      localStorage.removeItem(BASELINE_KEY);
      localStorage.removeItem(UPLOAD_KEY);
    } catch {
      /* noop */
    }
    set({
      userId: null,
      consentGiven: false,
      mode: 'care',
      uploadedTitle: null,
      uploadedContent: null,
      baselineScrollSpeed: null,
      isCalibrated: false,
    });
  },
}));

/** 온보딩 완료 여부 (라우터 가드용 · 스토어 인스턴스 밖에서도 호출 가능) */
export function isOnboarded(): boolean {
  return loadConsent();
}
