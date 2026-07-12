import { useState } from 'react';
import { AlertTriangle, Brain, BookOpen, Activity, Puzzle, Timer, Ruler, EyeOff, Edit3, Lightbulb, ArrowRight } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

export default function TutorialModal() {
  const { completeOnboarding } = useAuthStore();
  const [step, setStep] = useState(1);

  const handleNext = () => {
    if (step < 5) {
      setStep((prev) => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (step > 1) {
      setStep((prev) => prev - 1);
    }
  };

  const handleComplete = () => {
    completeOnboarding();
  };

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 backdrop-blur-xl"
      style={{ backgroundColor: 'rgba(255, 255, 255, 0.15)' }}
    >
      <div
        className="w-full max-w-2xl rounded-2xl border p-6 md:p-8 flex flex-col justify-between transition-all duration-300 relative overflow-hidden"
        style={{
          backgroundColor: 'var(--color-surface)',
          borderColor: 'var(--color-border)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.3)',
          minHeight: '480px',
        }}
      >
        {/* 상단 진행 표시바 */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-surface-alt flex">
          {[1, 2, 3, 4, 5].map((s) => (
            <div
              key={s}
              className="h-full flex-1 transition-all duration-300"
              style={{
                backgroundColor: s <= step ? 'var(--color-primary)' : 'transparent',
                opacity: s <= step ? 1 : 0.2,
              }}
            />
          ))}
        </div>

        {/* 튜토리얼 바디 */}
        <div className="flex-1 flex flex-col justify-center py-4">
          {step === 1 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span style={{ color: '#f43f5e' }}><AlertTriangle size={24} /></span>
                <span className="text-xs font-semibold uppercase tracking-wider text-rose-500">제작 배경 (Background)</span>
              </div>
              
              <div className="rounded-xl border p-4" style={{ backgroundColor: 'rgba(245, 158, 11, 0.08)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                <div className="flex items-start gap-3">
                  <div className="text-amber-500 mt-0.5"><AlertTriangle size={18} /></div>
                  <div>
                    <h3 className="text-sm font-bold text-amber-600 dark:text-amber-400 mb-1">튜토리얼 및 본편 진행 전 안내</h3>
                    <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                      너무 의식해서 잘 읽으려고 노력하지 마세요! 평소처럼 편안하고 자연스럽게 텍스트를 읽어주셔야 AI가 <strong>당신만의 진짜 독서 기준점(Baseline)</strong>을 정확하게 파악하고 맞춤형 케어를 제공할 수 있습니다.
                    </p>
                  </div>
                </div>
              </div>
              <h2 className="text-xl md:text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
                AI 시대, 무너지는 현대인의 기능적 문해력
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                OECD 성인역량평가(PIAAC) 결과, 한국인의 언어능력 점수가 10년 새 <b>273점(OECD 평균)에서 249점(평균 이하)으로 24점이나 급락</b>했습니다. 
                숏폼 콘텐츠와 AI 요약 비서에 텍스트 인지 부하를 외주화(Cognitive Offloading)하면서, 
                글을 스스로 깊이 읽고 성찰하는 비판적 사고 능력이 퇴화하고 있습니다.
              </p>

              {/* PIAAC 비교 막대 차트 (CSS 드로잉) */}
              <div className="rounded-xl border p-4 mt-2" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)' }}>
                <div className="text-xs font-semibold mb-3 text-center" style={{ color: 'var(--color-text-secondary)' }}>
                  📊 OECD PIAAC 성인 언어능력 점수 추이 (한국 vs OECD)
                </div>
                <div className="flex justify-around items-end h-28 pt-2">
                  {/* 1주기 한국 */}
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-[10px] font-bold text-gray-400 mb-1">273점</span>
                    <div className="w-8 rounded-t bg-gray-400/50" style={{ height: '70px' }} />
                    <span className="text-[10px] mt-1 text-gray-400">1주기('13) 한국</span>
                  </div>
                  {/* 1주기 OECD */}
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-[10px] font-bold text-gray-400 mb-1">273점</span>
                    <div className="w-8 rounded-t bg-gray-500/50" style={{ height: '70px' }} />
                    <span className="text-[10px] mt-1 text-gray-400">1주기 OECD 평균</span>
                  </div>
                  {/* 2주기 한국 */}
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-[10px] font-bold text-rose-500 mb-1">249점</span>
                    <div className="w-8 rounded-t bg-rose-400/80 transition-all duration-1000" style={{ height: '54px' }} />
                    <span className="text-[10px] mt-1 font-semibold text-rose-500">2주기('24) 한국</span>
                  </div>
                  {/* 2주기 OECD */}
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-[10px] font-bold text-gray-400 mb-1">260점</span>
                    <div className="w-8 rounded-t bg-gray-400/50" style={{ height: '62px' }} />
                    <span className="text-[10px] mt-1 text-gray-400">2주기 OECD 평균</span>
                  </div>
                </div>
                <div className="text-[10px] text-center mt-3 text-rose-500 font-medium flex items-center justify-center gap-1">
                  <AlertTriangle size={12} /> OECD 평균(260점)과 동일했던 지표가 10년 만에 평균 한참 아래로 역전 및 추락
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span style={{ color: 'var(--color-primary)' }}><Brain size={24} /></span>
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--color-primary)' }}>서비스 소개 (Introduction)</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
                스스로 생각하고 독독(讀讀)하는 문해력 페이스메이커
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                AllDayHappyDay는 AI가 글을 대신 요약하게 두지 않습니다. 
                사용자가 긴 글을 정독할 수 있도록 읽기 행동 패턴을 실시간 측정하고, 인지 저하가 감지되는 순간 
                필요한 개입(넛지 및 퀴즈)을 얹어주어 **스스로 읽고 이해하는 인지 뇌 근육**을 단단하게 지켜줍니다.
              </p>
              {/* Placeholder 그래픽 */}
              <div className="rounded-xl border p-6 mt-4 flex items-center justify-center" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', height: '140px' }}>
                <div className="text-center space-y-3">
                  <div className="flex items-center justify-center gap-4" style={{ color: 'var(--color-primary)' }}>
                    <BookOpen size={32} />
                    <ArrowRight size={20} style={{ color: 'var(--color-text-muted)' }} />
                    <Activity size={32} />
                    <ArrowRight size={20} style={{ color: 'var(--color-text-muted)' }} />
                    <Brain size={32} />
                  </div>
                  <div className="text-[11px] font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                    [ 읽기 행동 실시간 모니터링 ➔ 넛지 & O/X 퀴즈 개입 ➔ 비판적 성찰력 회복 ]
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span style={{ color: '#4ade80' }}><Puzzle size={24} /></span>
                <span className="text-xs font-semibold uppercase tracking-wider text-green-400">확장 프로그램 (Chrome Extension)</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
                웹 서핑 중 언제나 켜지는 인지 케어 보호막
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                크롬 익스텐션(Chrome Extension)을 연동하시면 뉴스 웹사이트, 기술 블로그, 논문 등 브라우저로 
                접하는 모든 문서에서 단어 사전 프리페치 서비스와 실시간 인지 넛지 시스템을 그대로 제공받으실 수 있습니다.
              </p>
              {/* Placeholder 그래픽 */}
              <div className="rounded-xl border p-6 mt-4 flex items-center justify-center" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', height: '140px' }}>
                <div className="text-center space-y-3">
                  <div className="flex items-center justify-center gap-2 text-xl font-bold" style={{ color: 'var(--color-primary)' }}>
                    <Puzzle size={28} /> Chrome Extension
                  </div>
                  <div className="text-[11px] border px-2 py-0.5 rounded-full inline-block" style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-secondary)' }}>
                    Chrome 웹 스토어에서 "AllDayHappyDay" 검색 후 다운로드
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span style={{ color: '#c084fc' }}><Activity size={24} /></span>
                <span className="text-xs font-semibold uppercase tracking-wider text-purple-400">집중도 지수 (Focus Score)</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
                내 집중 상태를 정밀하게 분석하는 지표
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                브라우저 창 활성화(Foreground) 여부, 사용자의 고유 읽기 속도 캘리브레이션 baseline 준수율, 
                단락별 적정 체류 시간 등을 슬라이딩 윈도우 기반으로 정교하게 추적하여 실시간 집중 지수(0~100점)를 계산합니다.
              </p>
              {/* Placeholder 그래픽 */}
              <div className="rounded-xl border p-4 mt-4" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)' }}>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 border rounded-lg flex flex-col items-center justify-center" style={{ borderColor: 'var(--color-border)' }}>
                    <div style={{ color: 'var(--color-primary)' }}><Timer size={24} /></div>
                    <div className="text-[10px] font-bold mt-2">체류 시간</div>
                  </div>
                  <div className="p-2 border rounded-lg flex flex-col items-center justify-center" style={{ borderColor: 'var(--color-border)' }}>
                    <div style={{ color: 'var(--color-primary)' }}><Ruler size={24} /></div>
                    <div className="text-[10px] font-bold mt-2">개인 baseline</div>
                  </div>
                  <div className="p-2 border rounded-lg flex flex-col items-center justify-center" style={{ borderColor: 'var(--color-border)' }}>
                    <div style={{ color: 'var(--color-danger, #ef4444)' }}><EyeOff size={24} /></div>
                    <div className="text-[10px] font-bold mt-2">이탈 감지</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span style={{ color: '#fbbf24' }}><Edit3 size={24} /></span>
                <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">문단 퀴즈 (Nudge & Quiz)</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
                집중이 흐려질 때, 가볍게 리프레시하는 O/X 퀴즈
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                글을 대충 훑어 읽거나 멍을 때리면 넛지(개입) 카드가 출현합니다. 
                이때 단락 핵심 내용을 간결하게 담은 O/X 퀴즈를 풀며 독서 몰입도를 끌어올리고 
                더 완벽하게 텍스트를 내 지식으로 성찰할 수 있습니다.
              </p>
              {/* Placeholder 그래픽 */}
              <div className="rounded-xl border p-6 mt-4 flex items-center justify-center" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', height: '140px' }}>
                <div className="text-center space-y-3">
                  <div className="flex items-center justify-center gap-2 text-xl font-bold" style={{ color: '#fbbf24' }}>
                    <Lightbulb size={24} /> Nudge Alert
                  </div>
                  <div className="text-[11px] px-3 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 inline-block font-semibold">
                    Q: 인쇄 텍스트 외 디지털 텍스트도 PIAAC의 리터러시 평가 대상인가요? (O / X)
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 하단 제어부 */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
          {/* 건너뛰기 */}
          <button
            onClick={handleComplete}
            className="text-xs font-semibold hover:underline"
            style={{ color: 'var(--color-text-muted)' }}
          >
            튜토리얼 건너뛰기
            <ArrowRight size={14} className="inline ml-1" />
          </button>

          {/* 이전 / 다음 페이징 */}
          <div className="flex items-center gap-2">
            {step > 1 && (
              <button
                onClick={handlePrev}
                className="px-4 py-1.5 rounded-md text-xs font-medium border"
                style={{
                  backgroundColor: 'transparent',
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text)',
                }}
              >
                이전
              </button>
            )}

            <button
              onClick={handleNext}
              className="px-4 py-1.5 rounded-md text-xs font-semibold text-white transition-colors"
              style={{
                backgroundColor: 'var(--color-primary)',
              }}
            >
              {step === 5 ? '완료하고 케어 시작하기 🎯' : '다음 단계'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
