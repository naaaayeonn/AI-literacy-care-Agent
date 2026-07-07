import React, { useState, useEffect, useRef } from 'react';
import { useFocusStore } from '../../stores/focusStore';
import { useReadingStore } from '../../stores/readingStore';
import { useScoreStore } from '../../stores/scoreStore';
import LevelBar from '../gamification/LevelBar';
import XpCounter from '../gamification/XpCounter';
import BadgeShelf from '../gamification/BadgeShelf';
import { getActiveWsClient } from '../../lib/ws';

// 집중도 수치에 따른 색상 매핑
function getFocusColor(score: number): string {
  if (score >= 80) return 'var(--color-engagement)';
  if (score >= 60) return 'var(--color-comprehension)';
  if (score >= 40) return 'var(--color-xp)';
  return 'var(--color-nudge-hard)';
}

function getFocusLabel(score: number): string {
  if (score >= 80) return '매우 집중';
  if (score >= 60) return '보통 집중';
  if (score >= 40) return '집중 저하';
  return '주의 필요';
}

export const FloatingControlPanel: React.FC = () => {
  const { focusScore, nudgeLevel, isQuizVisible } = useFocusStore();
  const { progress } = useReadingStore();
  const { literacyScore, xp, level, levelProgress } = useScoreStore();

  const focusColor = getFocusColor(focusScore);
  const focusLabel = getFocusLabel(focusScore);

  // ── 7/1 실시간 개입 로그 상태 ──
  const [logs, setLogs] = useState<{ id: string; time: string; msg: string; type: 'system' | 'nudge' | 'quiz' | 'xp' }[]>([]);
  const prevRef = useRef({ focusScore, nudgeLevel, isQuizVisible, progress, xp });
  const logContainerRef = useRef<HTMLDivElement>(null);
  const [isOnline, setIsOnline] = useState(false);
  const wasOnline = useRef(false);

  // 현재 시간 포맷팅 헬퍼
  const getNowString = () => {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
  };

  // 초기 로드 시 시스템 안내 메시지 추가
  useEffect(() => {
    setLogs([
      { id: 'init', time: getNowString(), msg: '🤖 리터러시 에이전트 오케스트레이터 가동 완료', type: 'system' }
    ]);
  }, []);

  // 7/6 추가: 실시간 WebSocket 연결 모니터링 및 연결 로그 출력
  useEffect(() => {
    const checkStatus = () => {
      const ws = getActiveWsClient();
      const online = !!(ws && ws.isConnected());
      if (online !== wasOnline.current) {
        if (online) {
          setLogs((prev) => [
            ...prev,
            { id: Math.random().toString(), time: getNowString(), msg: '🔌 백엔드 WebSocket 서버와 연결되었습니다.', type: 'system' as const }
          ].slice(-55));
        } else if (wasOnline.current) {
          setLogs((prev) => [
            ...prev,
            { id: Math.random().toString(), time: getNowString(), msg: '🔌 백엔드 연결 해제. 로컬 시뮬레이션 모드로 전환합니다.', type: 'system' as const }
          ].slice(-55));
        }
        wasOnline.current = online;
        setIsOnline(online);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  // 지표 모니터링을 통한 실시간 개입 로그 추가
  useEffect(() => {
    const prev = prevRef.current;
    const now = { focusScore, nudgeLevel, isQuizVisible, progress, xp };

    const addLog = (msg: string, type: 'system' | 'nudge' | 'quiz' | 'xp') => {
      setLogs((prevLogs) => [
        ...prevLogs,
        { id: Math.random().toString(), time: getNowString(), msg, type }
      ].slice(-55)); // 최대 55개 로그 유지
    };

    // 1. 읽기 진행률 로그
    if (now.progress !== prev.progress) {
      if (now.progress === 100) {
        addLog('🏆 본문 완독 성공! 최종 성과 분석 중...', 'system');
      } else if (now.progress > 0 && now.progress % 25 === 0) {
        addLog(`📖 읽기 진행도: ${now.progress}% 달성`, 'system');
      }
    }

    // 2. 집중도 변화 로그
    if (now.focusScore !== prev.focusScore) {
      if (now.focusScore < prev.focusScore) {
        addLog(`⚡ 집중도 감소 감지: ${prev.focusScore}% → ${now.focusScore}%`, 'system');
      } else {
        addLog(`⚡ 집중도 회복 감지: ${prev.focusScore}% → ${now.focusScore}%`, 'system');
      }
    }

    // 3. 넛지 레벨 개입 로그
    if (now.nudgeLevel !== prev.nudgeLevel) {
      if (now.nudgeLevel !== 'none') {
        addLog(`⚠️ [케어 개입] ${now.nudgeLevel.toUpperCase()} Nudge 전송 완료`, 'nudge');
      } else if (prev.nudgeLevel !== 'none') {
        addLog('✅ 개입 완화: Nudge 모니터링 대기 상태 진입', 'nudge');
      }
    }

    // 4. 돌발 퀴즈 팝업 로그
    if (now.isQuizVisible !== prev.isQuizVisible) {
      if (now.isQuizVisible) {
        addLog('🚨 [하드 개입] 문해력 점검 간이 퀴즈 트리거', 'quiz');
      } else {
        addLog('✅ 퀴즈 완료: 화면 인터럽트 해제', 'quiz');
      }
    }

    // 5. XP 누적 로그
    if (now.xp !== prev.xp) {
      const diff = now.xp - prev.xp;
      if (diff > 0) {
        addLog(`✨ 경험치 획득: +${diff} XP (누적: ${now.xp} XP)`, 'xp');
      }
    }

    prevRef.current = now;
  }, [focusScore, nudgeLevel, isQuizVisible, progress, xp]);

  // 새 로그가 오면 스크롤 제일 하단으로 이동
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div
      className={focusScore < 40 ? 'warning-pulse' : ''}
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        border: `1px solid ${focusScore < 40 ? 'var(--color-nudge-hard)' : 'var(--color-border)'}`,
        boxShadow: focusScore < 40 ? '0 0 16px rgba(240, 101, 62, 0.4)' : 'var(--shadow-md)',
        overflow: 'hidden',
        fontFamily: 'var(--font-sans)',
        transition: 'border-color 0.3s, box-shadow 0.3s',
      }}
    >
      {/* 집중력 저하 위험 시 경고 펄스 효과 주입 */}
      <style>{`
        @keyframes pulse-warning {
          0% { box-shadow: 0 0 0 0px rgba(240, 101, 62, 0.4); }
          70% { box-shadow: 0 0 0 10px rgba(240, 101, 62, 0); }
          100% { box-shadow: 0 0 0 0px rgba(240, 101, 62, 0); }
        }
        .warning-pulse {
          animation: pulse-warning 1.5s infinite;
        }
      `}</style>

      {/* 패널 헤더 */}
      <div
        style={{
          padding: 'var(--space-4) var(--space-5)',
          borderBottom: '1px solid var(--color-border)',
          background: focusScore < 40
            ? 'linear-gradient(135deg, var(--color-nudge-hard-tint), var(--color-surface))'
            : 'linear-gradient(135deg, var(--color-primary-tint), var(--color-surface))',
          transition: 'background 0.3s',
        }}
      >
        <p style={{
          fontSize: 'var(--text-xs)',
          fontWeight: 700,
          color: focusScore < 40 ? 'var(--color-nudge-hard)' : 'var(--color-primary)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}>
          {focusScore < 40 && <span className="animate-ping" style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-nudge-hard)' }} />}
          실시간 케어 제어판 {focusScore < 40 && '(주의 상태)'}
        </p>
      </div>

      <div style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>

        {/* ── 집중도 ── */}
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>⚡ 집중도</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{focusLabel}</span>
              <span style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: focusColor, fontVariantNumeric: 'tabular-nums' }}>
                {focusScore}%
              </span>
            </div>
          </div>
          <GaugeBar value={focusScore} color={focusColor} />
        </section>

        {/* ── 읽기 진행률 ── */}
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>📖 진행률</span>
            <span style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-primary)', fontVariantNumeric: 'tabular-nums' }}>
              {progress}%
            </span>
          </div>
          <GaugeBar value={progress} color="var(--color-primary)" />
        </section>

        {/* 구분선 */}
        <hr style={{ borderColor: 'var(--color-border)', margin: '0' }} />

        {/* ── Literacy Score ── */}
        <section>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)', fontWeight: 500 }}>🎯 리터러시 점수</p>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-1)' }}>
            <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-primary)', fontVariantNumeric: 'tabular-nums' }}>
              {literacyScore}
            </span>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', fontWeight: 500 }}>/ 100점</span>
          </div>
        </section>

        {/* ── 레벨 & XP ── */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <LevelBar level={level} percentage={levelProgress} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>누적 경험치</span>
            <XpCounter xp={xp} />
          </div>
        </section>

        {/* ── 배지 ── */}
        <section>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2.5)', fontWeight: 500 }}>🎖️ 배지 보유현황</p>
          <BadgeShelf compact />
        </section>

        {/* ── 7/1 추가: 실시간 에이전트 개입 로그 ── */}
        <section style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
              🤖 실시간 에이전트 개입 로그
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {isOnline ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="animate-pulse" style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-success)' }} />
                  <span style={{ fontSize: '9px', fontWeight: 700, color: 'var(--color-success)', letterSpacing: '0.05em' }}>ONLINE</span>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
                  <span style={{ fontSize: '9px', fontWeight: 700, color: '#f59e0b', letterSpacing: '0.05em' }}>OFFLINE</span>
                </div>
              )}
            </div>
          </div>
          <div
            ref={logContainerRef}
            style={{
              height: '110px',
              overflowY: 'auto',
              backgroundColor: 'var(--color-surface-alt)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              padding: '8px 10px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              fontFamily: 'monospace',
              fontSize: '10px',
              lineHeight: '1.4',
            }}
          >
            {logs.length === 0 ? (
              <div style={{ color: 'var(--color-text-muted)', fontStyle: 'italic', textAlign: 'center', marginTop: '30px' }}>
                로그 대기 중...
              </div>
            ) : (
              logs.map((log) => {
                let color = 'var(--color-text)';
                if (log.type === 'nudge') color = 'var(--color-nudge-medium)';
                if (log.type === 'quiz') color = 'var(--color-nudge-hard)';
                if (log.type === 'xp') color = 'var(--color-xp)';
                return (
                  <div key={log.id} style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
                    <span style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>[{log.time}]</span>
                    <span style={{ color, fontWeight: log.type !== 'system' ? 600 : 400 }}>{log.msg}</span>
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* ── 데모 시뮬레이터 ── */}
        <section style={{ borderTop: '1px dashed var(--color-border)', paddingTop: 'var(--space-4)' }}>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
            🎮 집중도 시뮬 (데모용)
          </p>
          <FocusSimulator />
        </section>

      </div>
    </div>
  );
};

/** 공통 게이지 바 */
function GaugeBar({ value, color }: { value: number; color: string }) {
  return (
    <div
      style={{
        height: '8px',
        borderRadius: 'var(--radius-full)',
        backgroundColor: 'var(--color-surface-alt)',
        border: '1px solid var(--color-border)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${Math.min(100, value)}%`,
          borderRadius: 'var(--radius-full)',
          background: color,
          transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      />
    </div>
  );
}

export default FloatingControlPanel;

/**
 * FocusSimulator — 데모·심사 시연용 집중도 직접 조작 및 자동 E2E 시연기
 */
function FocusSimulator() {
  const { setFocusScore, dismissNudge, dismissQuiz, isQuizVisible } = useFocusStore();
  const { setProgress } = useReadingStore();
  const { restartDemoSession, quizResults, recordQuizResult, addXp } = useScoreStore();

  const [demoStep, setDemoStep] = useState<number | null>(null);
  const [demoStatus, setDemoStatus] = useState<string>('');
  const timeoutIds = useRef<number[]>([]);

  const clearAllTimeouts = () => {
    timeoutIds.current.forEach((id) => window.clearTimeout(id));
    timeoutIds.current = [];
  };

  useEffect(() => {
    return () => clearAllTimeouts();
  }, []);

  // 퀴즈 결과가 추가되면 데모 Step 4에서 자동으로 Step 5로 이동
  useEffect(() => {
    if (demoStep === 4 && quizResults.length > 0) {
      proceedToStep5();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizResults.length, demoStep]);

  const resetAll = () => {
    clearAllTimeouts();
    setDemoStep(null);
    setDemoStatus('');
    setProgress(0);
    setFocusScore(85);
    dismissNudge();
    dismissQuiz();
    restartDemoSession();
  };

  const proceedToStep5 = () => {
    clearAllTimeouts();
    setDemoStep(5);
    setDemoStatus('✨ 퀴즈 정답! 집중도 회복 및 90% 돌파');
    setFocusScore(85);
    dismissNudge();
    dismissQuiz();
    setProgress(90);

    const t1 = window.setTimeout(() => {
      setDemoStep(6);
      setDemoStatus('🎉 완독 완료! 최종 결과 분석');
      setProgress(100);
      setDemoStep(null);
    }, 3000);
    timeoutIds.current.push(t1);
  };

  const handleAutoAnswer = () => {
    recordQuizResult({
      quizId: 'mock-q1',
      correct: true,
      xpAwarded: 30,
      timestamp: Date.now(),
    });
    addXp(30);
  };

  const startAutoDemo = () => {
    resetAll();
    setDemoStep(0);
    setDemoStatus('📖 E2E 데모 시작: 독서 중... (집중도 85)');

    const t1 = window.setTimeout(() => {
      setDemoStep(1);
      setDemoStatus('📊 25% 지점 통과 (점수 기록)');
      setProgress(25);
    }, 2500);

    const t2 = window.setTimeout(() => {
      setDemoStep(2);
      setDemoStatus('⚠️ 집중력 저하 감지 → Soft Nudge 작동');
      setProgress(35);
      setFocusScore(65);
    }, 5500);

    const t3 = window.setTimeout(() => {
      setDemoStep(3);
      setDemoStatus('⚠️ 추가 저하 → Medium Nudge (요약 힌트)');
      setProgress(50);
      setFocusScore(45);
    }, 9000);

    const t4 = window.setTimeout(() => {
      setDemoStep(4);
      setDemoStatus('🚨 주의 필요 → Hard Nudge + 퀴즈 팝업');
      setProgress(75);
      setFocusScore(25);
    }, 13000);

    timeoutIds.current.push(t1, t2, t3, t4);
  };

  const steps = [
    { label: '집중 (85)', score: 85, color: 'var(--color-engagement)' },
    { label: 'Soft (65)', score: 65, color: 'var(--color-nudge-soft)' },
    { label: 'Medium (45)', score: 45, color: 'var(--color-nudge-medium)' },
    { label: 'Hard (25)', score: 25, color: 'var(--color-nudge-hard)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* 수동 집중도 조작 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
        {steps.map(({ label, score, color }) => (
          <button
            key={label}
            onClick={() => {
              clearAllTimeouts();
              setDemoStep(null);
              setDemoStatus('');
              setFocusScore(score);
            }}
            style={{
              padding: '6px 4px',
              fontSize: '10px',
              fontFamily: 'var(--font-sans)',
              fontWeight: 600,
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${color}`,
              backgroundColor: 'var(--color-surface)',
              color,
              cursor: 'pointer',
              transition: 'background-color 0.2s',
              textAlign: 'center',
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-surface-alt)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-surface)')}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 데모 제어 및 자동 데모 버튼 */}
      <div style={{ display: 'flex', gap: '6px' }}>
        {demoStep === null ? (
          <button
            onClick={startAutoDemo}
            style={{
              flex: 1,
              padding: '8px',
              fontSize: '11px',
              fontFamily: 'var(--font-sans)',
              fontWeight: 700,
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-primary)',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
            }}
          >
            🤖 자동 E2E 데모 시작
          </button>
        ) : (
          <button
            onClick={resetAll}
            style={{
              flex: 1,
              padding: '8px',
              fontSize: '11px',
              fontFamily: 'var(--font-sans)',
              fontWeight: 700,
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-nudge-hard)',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            ⏹️ 데모 중지 / 리셋
          </button>
        )}

        <button
          onClick={resetAll}
          style={{
            padding: '8px 10px',
            fontSize: '11px',
            fontFamily: 'var(--font-sans)',
            fontWeight: 600,
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-surface-alt)')}
          onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-surface)')}
        >
          🔄 리셋
        </button>
      </div>

      {/* 데모 진행 정보 */}
      {demoStep !== null && (
        <div
          style={{
            padding: '8px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--color-primary-tint)',
            border: '1px solid var(--color-border)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          <p style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-primary)', marginBottom: '2px' }}>
            [E2E 시연 시나리오 진행 중]
          </p>
          <p style={{ fontSize: '11px', color: 'var(--color-text)', lineHeight: '1.4' }}>
            {demoStatus}
          </p>
          {demoStep === 4 && isQuizVisible && (
            <div style={{ marginTop: '6px', display: 'flex', gap: '4px' }}>
              <button
                onClick={handleAutoAnswer}
                style={{
                  flex: 1,
                  padding: '4px',
                  fontSize: '9px',
                  fontFamily: 'var(--font-sans)',
                  fontWeight: 700,
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--color-comprehension)',
                  color: '#fff',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                💡 자동 정답 제출 후 계속
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
