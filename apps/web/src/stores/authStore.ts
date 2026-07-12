import { create } from 'zustand';

export interface LocalUser {
  id: string;
  email: string;
  nickname: string;
  createdAt: string;
  onboardingCompleted: boolean;
}

interface AuthState {
  user: LocalUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  signUp: (email: string, password: string, nickname: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  checkSession: () => void;
  completeOnboarding: () => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

const USERS_KEY = 'local_users_db';
const SESSION_KEY = 'local_session_uid';

// Helper: 로컬 사용자 목록 로드
function getLocalUsers(): Record<string, LocalUser & { passwordHash: string }> {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

// Helper: 로컬 사용자 저장
function saveLocalUsers(users: Record<string, LocalUser & { passwordHash: string }>) {
  try {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  } catch (e) {
    console.error('Failed to save local users to localStorage', e);
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  signUp: async (email, password, nickname) => {
    set({ isLoading: true, error: null });
    try {
      const users = getLocalUsers();
      
      // 이메일 중복 검사
      const isDuplicate = Object.values(users).some((u) => u.email === email);
      if (isDuplicate) {
        throw new Error('이미 등록된 이메일 주소입니다.');
      }

      // 새 유저 생성 (UUID 대체용 랜덤 스트링)
      const userId = 'u_user_' + Math.random().toString(36).substr(2, 9);
      const newUser = {
        id: userId,
        email,
        nickname,
        createdAt: new Date().toISOString(),
        onboardingCompleted: false,
        passwordHash: btoa(password), // 간단한 base64 해싱
      };

      users[userId] = newUser;
      saveLocalUsers(users);

      // 가입 성공 후 즉시 자동 로그인 처리
      localStorage.setItem(SESSION_KEY, userId);
      set({ 
        user: {
          id: newUser.id,
          email: newUser.email,
          nickname: newUser.nickname,
          createdAt: newUser.createdAt,
          onboardingCompleted: newUser.onboardingCompleted,
        },
        isAuthenticated: true,
        isLoading: false, 
      });
    } catch (err: any) {
      set({ error: err.message || '회원가입에 실패했습니다.', isLoading: false });
      throw err;
    }
  },

  signIn: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const users = getLocalUsers();
      const targetUser = Object.values(users).find(
        (u) => u.email === email && u.passwordHash === btoa(password)
      );

      if (!targetUser) {
        throw new Error('이메일 또는 비밀번호가 올바르지 않습니다.');
      }

      localStorage.setItem(SESSION_KEY, targetUser.id);
      set({
        user: {
          id: targetUser.id,
          email: targetUser.email,
          nickname: targetUser.nickname,
          createdAt: targetUser.createdAt,
          onboardingCompleted: targetUser.onboardingCompleted,
        },
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message || '로그인에 실패했습니다.', isLoading: false });
      throw err;
    }
  },

  signOut: () => {
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch {
      /* noop */
    }
    set({ user: null, isAuthenticated: false, error: null });
    window.location.href = '/'; // Hard reload to clear all Zustand stores from memory
  },

  checkSession: () => {
    try {
      const currentUid = localStorage.getItem(SESSION_KEY);
      if (!currentUid) {
        set({ user: null, isAuthenticated: false });
        return;
      }

      const users = getLocalUsers();
      const sessionUser = users[currentUid];

      if (sessionUser) {
        set({
          user: {
            id: sessionUser.id,
            email: sessionUser.email,
            nickname: sessionUser.nickname,
            createdAt: sessionUser.createdAt,
            onboardingCompleted: sessionUser.onboardingCompleted,
          },
          isAuthenticated: true,
        });
      } else {
        localStorage.removeItem(SESSION_KEY);
        set({ user: null, isAuthenticated: false });
      }
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },

  completeOnboarding: () => {
    try {
      const currentUid = localStorage.getItem(SESSION_KEY);
      if (!currentUid) return;

      const users = getLocalUsers();
      if (users[currentUid]) {
        users[currentUid].onboardingCompleted = true;
        saveLocalUsers(users);

        set((state) => ({
          user: state.user ? { ...state.user, onboardingCompleted: true } : null,
        }));
        console.log('[AUTH] Onboarding completed status saved locally.');
      }
    } catch (e) {
      console.error('Failed to update onboarding complete status', e);
    }
  },
}));
