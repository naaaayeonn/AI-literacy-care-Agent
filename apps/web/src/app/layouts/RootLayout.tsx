import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useFocusStore } from '../../stores/focusStore';
import { useReadingStore } from '../../stores/readingStore';
import { useAuthStore } from '../../stores/authStore';
import TutorialModal from '../../components/common/TutorialModal';

/**
 * RootLayout — 6/22 스토어 연결 업데이트
 * 헤더의 집중도·진행률 StatusPill이 실시간으로 스토어 값을 구독함.
 */
export default function RootLayout() {
  const location = useLocation();
  const isReading = location.pathname === '/reading';

  // 헤더 StatusPill용 스토어 구독
  const focusScore = useFocusStore((s) => s.focusScore);
  const progress = useReadingStore((s) => s.progress);

  // 7/11: 로컬 인증 상태 및 온보딩 여부 구독
  const { user, isAuthenticated } = useAuthStore();

  return (
    <div
      className="min-h-screen transition-colors duration-200"
      style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
    >
      {/* ── 헤더 ── */}
      <header
        className="sticky top-0 z-panel border-b"
        style={{
          backgroundColor: 'var(--color-surface)',
          borderColor: 'var(--color-border)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          {/* 로고 */}
          <div className="flex items-center gap-2">
            <span className="text-xl select-none">🧠</span>
            <span
              className="font-semibold text-base hidden sm:block"
              style={{
                fontFamily: 'var(--font-sans)',
                color: 'var(--color-primary)',
                letterSpacing: 'var(--tracking-kr)',
              }}
            >
              AI 리터러시 케어
            </span>
          </div>

          {/* 네비게이션 */}
          <nav className="flex items-center gap-1">
            <NavLink
              to="/reading"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-tint text-primary'
                    : 'text-text-secondary hover:text-text hover:bg-surface-alt'
                }`
              }
              style={{ fontFamily: 'var(--font-sans)' } as React.CSSProperties}
            >
              📖 읽기
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-tint text-primary'
                    : 'text-text-secondary hover:text-text hover:bg-surface-alt'
                }`
              }
              style={{ fontFamily: 'var(--font-sans)' } as React.CSSProperties}
            >
              📊 성장 대시보드
            </NavLink>
            <NavLink
              to="/profile"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-tint text-primary'
                    : 'text-text-secondary hover:text-text hover:bg-surface-alt'
                }`
              }
              style={{ fontFamily: 'var(--font-sans)' } as React.CSSProperties}
            >
              🕶️ 내 프로필
            </NavLink>
            <NavLink
              to="/home"
              className="px-3 py-1.5 rounded-md text-sm font-medium transition-colors text-text-secondary hover:text-text hover:bg-surface-alt"
              style={{ fontFamily: 'var(--font-sans)' } as React.CSSProperties}
            >
              ＋ 새 세션
            </NavLink>
          </nav>

          {/* 헤더 우측 실시간 상태 표시 (읽기 중일 때만) */}
          {isReading && (
            <div className="hidden md:flex items-center gap-3">
              <StatusPill label="집중도" value={`${focusScore}%`} color="var(--color-engagement)" />
              <StatusPill label="진행률" value={`${progress}%`} color="var(--color-primary)" />
            </div>
          )}
        </div>
      </header>

      {/* ── 페이지 콘텐츠 ── */}
      <main>
        <Outlet />
      </main>

      {/* 7/11: 초기 가입자 온보딩 튜토리얼 모달 오버레이 */}
      {isAuthenticated && user && !user.onboardingCompleted && <TutorialModal />}
    </div>
  );
}

/** 헤더 상태 알약 컴포넌트 */
function StatusPill({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs"
      style={{
        backgroundColor: 'var(--color-surface-alt)',
        borderColor: 'var(--color-border)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
      <span
        className="font-semibold tabular-nums"
        style={{ color, transition: 'color 0.3s' }}
      >
        {value}
      </span>
    </div>
  );
}
