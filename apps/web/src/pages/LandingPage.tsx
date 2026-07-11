/**
 * LandingPage — '/home'
 * 온보딩 이후 모드 선택 화면.
 *  - 실시간 케어 ON : 인앱 리더에서 집중도 추적 + 넛지 + 퀴즈 (데모 메인)
 *  - 페이지 업로드   : URL/텍스트를 붙여넣어 내 문서로 케어
 *  - 확장 설치 CTA   : 실제 크롬/PDF 브라우징에 케어 적용
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionConfig } from '../stores/sessionConfigStore';
import { useAuthStore } from '../stores/authStore';
import TutorialModal from '../components/common/TutorialModal';
import BottomTabBar from '../components/common/BottomTabBar';

export default function LandingPage() {
  const navigate = useNavigate();
  const userId = useSessionConfig((s) => s.userId);
  
  
  // 7/11: 로컬 인증 상태 구독
  const { user, isAuthenticated } = useAuthStore();

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 모드 선택';
  }, []);

  const startCare = () => {
    navigate('/upload');
  };


  const shortId = userId ? userId.replace('u_anon_', '').slice(0, 8) : 'guest';

  return (
    <div
      className="min-h-screen px-4 pt-10 pb-24"
      style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
    >
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2">
            <span className="text-2xl select-none">🧠</span>
            <span className="font-semibold" style={{ color: 'var(--color-primary)' }}>
              AI 리터러시 케어
            </span>
          </div>
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
            style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}
          >
            <span>🕶️</span>
            <span style={{ color: 'var(--color-text-secondary)' }}>익명</span>
            <span className="font-semibold tabular-nums" style={{ color: 'var(--color-text)' }}>#{shortId}</span>
          </div>
        </div>

        <h1 className="text-2xl font-bold mb-1" style={{ letterSpacing: 'var(--tracking-kr)' }}>
          어떻게 케어를 시작할까요?
        </h1>
        <p className="text-sm mb-8" style={{ color: 'var(--color-text-secondary)' }}>
          읽을 콘텐츠를 고르면 실시간으로 집중도를 측정하고 맞춤 개입을 제공합니다.
        </p>

        {/* 가로 1:1 대칭 배치 모드 카드 2열 */}
        <div className="grid gap-4 sm:grid-cols-2 mb-6 items-stretch">
          <ModeCard
            emoji="⚡"
            title="실시간 케어 ON"
            desc="업로드한 문서의 읽기 행동 패턴(스크롤, 체류 시간, 이탈 등)을 실시간 추적하여 문맥 설명 넛지와 단락 퀴즈를 케어해 줍니다."
            badge="가장 빠른 체험"
            accent="var(--color-engagement)"
            onClick={startCare}
          />
          <ModeCard
            emoji="🧩"
            title="크롬 확장 프로그램"
            desc="크롬 확장 프로그램을 설치하면 내가 실제로 보는 웹페이지나 PDF 문서에서도 실시간 집중도 측정과 퀴즈 개입 케어가 그대로 적용됩니다."
            badge="확장 설치 안내"
            accent="var(--color-primary)"
            onClick={() => navigate('/upload?ext=1')}
          />
        </div>


      </div>

      {/* 7/11: 초기 가입자 온보딩 튜토리얼 모달 오버레이 */}
      {isAuthenticated && user && !user.onboardingCompleted && <TutorialModal />}

      {/* 7/11: 하단 탭 네비게이션 바 */}
      <BottomTabBar />
    </div>
  );
}

function ModeCard({
  emoji,
  title,
  desc,
  badge,
  accent,
  onClick,
}: {
  emoji: string;
  title: string;
  desc: string;
  badge: string;
  accent: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="text-left rounded-xl border p-6 transition-transform hover:-translate-y-0.5"
      style={{
        backgroundColor: 'var(--color-surface)',
        borderColor: 'var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
        cursor: 'pointer',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-3xl select-none">{emoji}</span>
        <span
          className="text-xs px-2 py-0.5 rounded-full font-medium"
          style={{ backgroundColor: 'var(--color-surface-alt)', color: accent, border: `1px solid ${accent}` }}
        >
          {badge}
        </span>
      </div>
      <div className="font-semibold text-lg mb-1" style={{ letterSpacing: 'var(--tracking-kr)' }}>
        {title}
      </div>
      <p className="text-sm" style={{ color: 'var(--color-text-secondary)', lineHeight: 'var(--leading-normal)' }}>
        {desc}
      </p>
      <div className="mt-4 text-sm font-medium" style={{ color: accent }}>
        선택하기 →
      </div>
    </button>
  );
}
