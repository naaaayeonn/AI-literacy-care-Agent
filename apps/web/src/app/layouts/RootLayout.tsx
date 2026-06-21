import { Outlet, NavLink, useLocation } from 'react-router-dom';

/**
 * RootLayout — 모든 페이지 공통 헤더 + 레이아웃 셸
 */
export default function RootLayout() {
  const location = useLocation();
  const isReading = location.pathname === '/reading';

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
          </nav>

          {/* 헤더 우측 상태 표시 (읽기 중일 때만) */}
          {isReading && (
            <div className="hidden md:flex items-center gap-3">
              <StatusPill label="집중도" value="85%" color="var(--color-primary)" />
              <StatusPill label="진행률" value="42%" color="var(--color-engagement)" />
            </div>
          )}
        </div>
      </header>

      {/* ── 페이지 콘텐츠 ── */}
      <main>
        <Outlet />
      </main>
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
      <span className="font-semibold" style={{ color }}>{value}</span>
    </div>
  );
}
