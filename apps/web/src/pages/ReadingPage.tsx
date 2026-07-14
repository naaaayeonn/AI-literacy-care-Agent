import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSessionConfig } from '../stores/sessionConfigStore';
import ReadingPane from '../components/reading/ReadingPane';
import FloatingControlPanel from '../components/panel/FloatingControlPanel';
import NudgeController from '../components/nudge/NudgeController';
import SessionSummaryCard from '../components/dashboard/SessionSummaryCard';
import { Card } from '../components/common/Card';
import { useReadingStore } from '../stores/readingStore';
import { useScoreEngine } from '../lib/useScoreEngine';
import { useFocusStore } from '../stores/focusStore';
import { useScoreStore } from '../stores/scoreStore';
import { useAuthStore } from '../stores/authStore';
import { api } from '../lib/api';

/**
 * ReadingPage — /reading
 * 6/24: NudgeController 연결 — 폐루프 실시간 개입 시스템
 * 6/26: useScoreEngine 연결 — 실시간 Literacy Score 계산 + 차트 자동 갱신
 *       SessionSummaryCard — 완독(progress >= 100) 시 결과 카드 표시
 */
export default function ReadingPage() {
  const progress = useReadingStore((s) => s.progress);
  const sessionId = useReadingStore((s) => s.sessionId);
  const startSessionStore = useReadingStore((s) => s.startSession);
  const setProgress = useReadingStore((s) => s.setProgress);
  const setHighlights = useReadingStore((s) => s.setHighlights);
  const setTermDefinition = useReadingStore((s) => s.setTermDefinition);

  const showNudge = useFocusStore((s) => s.showNudge);
  const setActiveQuizzes = useFocusStore((s) => s.setActiveQuizzes);
  const showQuiz = useFocusStore((s) => s.showQuiz);
  const setFocusScore = useFocusStore((s) => s.setFocusScore);

  const clearQueue = useReadingStore((s) => s.clearQueue);

  // 6/26: Score Engine 마운트 (ReadingPage 수명 동안 실행)
  useScoreEngine();

  const navigate = useNavigate();

  // 온보딩(익명 로그인+동의) 미완료 시 진입 차단
  useEffect(() => {
    if (!useSessionConfig.getState().consentGiven) {
      navigate('/onboarding', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 읽기';
  }, []);

  // 완독 시 세션 최종 저장 및 결과 가져오기
  useEffect(() => {
    if (progress >= 100 && sessionId && !useScoreStore.getState().isFinalized) {
      console.log('[ReadingPage] Session finished! Finalizing on backend...');
      const currentScores = useScoreStore.getState();
      
      const finalize = async () => {
        useScoreStore.getState().setFinalizing(true);
        try {
          await api.finishSession(sessionId, {
            literacy_score: currentScores.literacyScore,
            comprehension_score: currentScores.comprehensionScore,
            engagement_score: currentScores.engagementScore,
          });
          
          const scoreResult = await api.getSessionResult(sessionId);
          
          useScoreStore.setState({
            isFinalized: true,
            literacyScore: scoreResult.literacyScore,
            comprehensionScore: scoreResult.comprehensionScore,
            engagementScore: scoreResult.engagementScore,
            literacyDomains: scoreResult.literacyDomains ?? null,
            textProfile: scoreResult.textProfile ?? null,
            xp: scoreResult.totalXp,
            level: scoreResult.level,
            scoreSeries: scoreResult.scoreSeries.map((s) => ({
              label: s.label,
              before: s.before,
              after: s.after,
            })),
            badges: scoreResult.badges.map((b) => ({
              id: b.id,
              name: b.name,
              emoji: b.emoji,
              description: b.description,
              acquiredAt: b.acquiredAt,
            })),
          });
          console.log('[ReadingPage] Session finalization completed.');
        } catch (err) {
          console.error('[ReadingPage] Failed to finalize reading session:', err);
        } finally {
          useScoreStore.getState().setFinalizing(false);
        }
      };
      
      finalize();
    }
  }, [progress, sessionId]);

  // 7/14: 컴포넌트 언마운트(페이지 이탈) 시 세션 최종 저장 (완독 전에 페이지를 나갈 때도 데이터가 누실되지 않게 처리)
  useEffect(() => {
    return () => {
      const currentScores = useScoreStore.getState();
      const sId = useReadingStore.getState().sessionId;
      const finalized = useScoreStore.getState().isFinalized;
      
      if (sId && !finalized) {
        console.log('[ReadingPage] Page unmounting. Auto-finalizing session...');
        useScoreStore.getState().setFinalizing(true);
        // 남아있는 이벤트 큐가 있다면 최신 상태 전송
        const remainingQueue = useReadingStore.getState().eventQueue;
        if (remainingQueue.length > 0) {
          api.sendEvents(sId, remainingQueue).catch(() => {});
          useReadingStore.getState().clearQueue();
        }
        
        api.finishSession(sId, {
          literacy_score: currentScores.literacyScore,
          comprehension_score: currentScores.comprehensionScore,
          engagement_score: currentScores.engagementScore,
        }).catch((err) => {
          console.error('[ReadingPage] Failed to auto-finalize session on unmount:', err);
        }).finally(() => {
          useScoreStore.getState().setFinalizing(false);
        });
      }
    };
  }, []);

  // 7/8: 실시간 REST /events 배치 폴링 & 개입 커맨드 처리 (WebSocket 제거)
  useEffect(() => {
    let active = true;
    let flushIntervalId: any = null;
    let currentSessionId: string | null = null;

    // 개입 명령 처리 핸들러 (Intervention Command → UI)
    const handleInterventionCommand = (command: any) => {
      if (!command) return;
      console.log('[ReadingPage] ← Received REST Intervention Command:', command);
      
      // 모든 커맨드에 대해 점수 및 진행률 업데이트를 공통으로 수행
      if (command.payload && command.payload.focusScore !== undefined) {
        setFocusScore(command.payload.focusScore);
      }
      if (command.payload && command.payload.progress !== undefined) {
        setProgress(command.payload.progress);
      }

      switch (command.type) {
        case 'nudge':
          if (command.payload.nudgeLevel) {
            showNudge(command.payload.nudgeLevel, command.payload.nudgeMessage, command.payload.summaryText);
          }
          break;
        case 'quiz':
          if (command.payload.quizzes) {
            setActiveQuizzes(command.payload.quizzes);
            showQuiz();
          }
          break;
        case 'highlight':
          if (command.payload.highlights) {
            const indices = command.payload.highlights.map((h: any) => h.paragraphIndex);
            setHighlights(indices);
          }
          break;
        case 'score_update':
          // 점수는 이미 위에서 공통으로 업데이트됨
          break;
        case 'session_end':
          if (currentSessionId) {
            api.getSessionResult(currentSessionId)
              .then((scoreResult) => {
                if (!active) return;
                useScoreStore.setState({
                  isFinalized: true,
                  literacyScore: scoreResult.literacyScore,
                  comprehensionScore: scoreResult.comprehensionScore,
                  engagementScore: scoreResult.engagementScore,
                  literacyDomains: scoreResult.literacyDomains ?? null,
                  textProfile: scoreResult.textProfile ?? null,
                  xp: scoreResult.totalXp,
                  level: scoreResult.level,
                  scoreSeries: scoreResult.scoreSeries.map((s) => ({
                    label: s.label,
                    before: s.before,
                    after: s.after,
                  })),
                  badges: scoreResult.badges.map((b) => ({
                    id: b.id,
                    name: b.name,
                    emoji: b.emoji,
                    description: b.description,
                    acquiredAt: b.acquiredAt,
                  })),
                });
              })
              .catch((err) => {
                console.error('[ReadingPage] Failed to fetch session result:', err);
              });
          }
          setProgress(100);
          break;
        default:
          console.warn('[ReadingPage] Unknown command type:', command.type);
      }
    };

    // 큐에 있는 이벤트를 서버로 Flush 전송
    const flushQueue = async () => {
      // 컴포넌트 마운트 해제 또는 세션 ID가 없을 경우 전송하지 않음
      const currentQueue = useReadingStore.getState().eventQueue;
      if (!active || !currentSessionId || currentQueue.length === 0) return;

      // 큐 선점 비우기
      const eventsToSend = [...currentQueue];
      clearQueue();

      try {
        const cmd = await api.sendEvents(currentSessionId, eventsToSend);
        if (active) {
          handleInterventionCommand(cmd);
        }
      } catch (err) {
        console.warn('[ReadingPage] Failed to send events, keeping in queue:', err);
        // 실패 시 큐에 다시 넣기 (순서 보장 위해 앞쪽에 넣는 것이 이상적이나, 간단히 다시 enqueue)
        eventsToSend.forEach(e => useReadingStore.getState().enqueueEvent(e));
      }
    };

    async function initSession() {
      // 7/13: 새 글을 읽을 때 이전 집중도와 상태가 유지되는 버그 수정
      useFocusStore.getState().reset();
      useReadingStore.getState().reset();
      useScoreStore.getState().reset();
      try {
        const cfg = useSessionConfig.getState();
        const isUpload =
          cfg.mode === 'upload' && !!cfg.uploadedContent && cfg.uploadedContent.length > 0;

        const loggedInUser = useAuthStore.getState().user;
        const activeUserId = loggedInUser?.id || cfg.userId || 'u_anon_guest';

        // 7/15: 업로드 세션이면 백엔드 응답(재청킹)을 기다리는 동안 데모(sampleArticle)가
        // 잠깐이라도 보이지 않도록, 저장된 원문을 즉시 렌더한다. (응답이 오면 아래에서 정교화)
        if (isUpload && cfg.uploadedContent && cfg.uploadedContent.length) {
          useReadingStore.getState().setArticle({
            id: 'uploaded',
            title: cfg.uploadedTitle ?? '내가 올린 문서',
            category: '내 업로드',
            author: '익명 업로드',
            publishedAt: '방금',
            content: cfg.uploadedContent,
          });
        }

        const sessionData = await api.startSession({
          articleId: isUpload ? 'uploaded' : 'default-article',
          userId: activeUserId,
          content: isUpload ? cfg.uploadedContent! : undefined,
          baselineScrollSpeed: cfg.baselineScrollSpeed ?? undefined,
        });

        if (!active) return;

        currentSessionId = sessionData.sessionId;
        // Zustand store 세션 연동 시작
        startSessionStore(sessionData.article.id, sessionData.sessionId);

        // 업로드 모드: 백엔드(2번)가 재구성한 쉬운 문장(restructuredText)을 원문과 함께 저장
        // → 리더의 '쉬운 문장 보기' 토글이 업로드한 문서에도 작동
        if (isUpload) {
          const chunks: any[] = (sessionData.article as any)?.chunks ?? [];
          const originals = chunks.map((c: any) => c.original_text || c.originalText).filter(Boolean);
          const easies = chunks.map((c: any) => c.restructured_text || c.restructuredText || c.original_text || c.originalText);
          // 7/15: 백엔드가 chunks를 못 주거나(콜드스타트·실패·mock 폴백) 응답이 비어도
          // 데모(sampleArticle)로 떨어지지 않도록, localStorage에 영속된 업로드 원문으로 폴백한다.
          // "새로고침하면 업로드가 데모로 돌아가던" 문제의 최종 방어선.
          const content = originals.length ? originals : (cfg.uploadedContent ?? []);
          if (content.length) {
            useReadingStore.getState().setArticle({
              id: sessionData.article.id ?? 'uploaded',
              title: cfg.uploadedTitle ?? '내가 올린 문서',
              category: '내 업로드',
              author: '익명 업로드',
              publishedAt: '방금',
              content,
              contentEasy: originals.length ? easies : content,
            });
          }
        }

        // 7/5 추가: AI RAG 설명 사전 프리페치
        const termsToPrefetch = [
          '디지털 리터러시',
          'LLM',
          '환각 현상',
          '인지부하',
          '넛지',
          'Literacy Score',
        ];

        termsToPrefetch.forEach((term) => {
          api.getTermDefinition(sessionData.sessionId, term)
            .then((res) => {
              if (active) {
                setTermDefinition(term, res.explanation);
              }
            })
            .catch((err) => {
              console.error(`[ReadingPage] Failed to prefetch term '${term}':`, err);
            });
        });

        // 1.5초(1500ms) 주기적 배치 Flush 루프 시작
        flushIntervalId = setInterval(flushQueue, 1500);
      } catch (err) {
        console.error('[ReadingPage] Failed to initialize session REST APIs:', err);
      }
    }

    initSession();

    // 큐 변경 실시간 감시 (blur·dwell·focus 이입 시 즉시 flush)
    // 7/15: 'focus'(탭 복귀)도 즉시 flush 대상에 추가. 탭 이탈 중 보낸 blur의 감점 결과가
    // 백그라운드에서 지연 처리되어 화면에 안 보이던 것을, 복귀 순간 재요청해 확실히 반영한다.
    const unsubscribeQueue = useReadingStore.subscribe((state) => {
      const queue = state.eventQueue;
      if (queue.length > 0) {
        const lastEvent = queue[queue.length - 1];
        if (lastEvent.type === 'blur' || lastEvent.type === 'dwell' || lastEvent.type === 'focus') {
          flushQueue();
        }
      }
    });

    return () => {
      active = false;
      if (flushIntervalId) {
        clearInterval(flushIntervalId);
      }
      unsubscribeQueue();
      // 마지막 남은 잔여 이벤트 전송 시도
      flushQueue();
    };
  }, [
    startSessionStore,
    showNudge,
    setActiveQuizzes,
    showQuiz,
    setHighlights,
    setFocusScore,
    setProgress,
    clearQueue,
  ]);

  const isFinished = progress >= 100;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      {/* ── 폐루프 개입 시스템 ── */}
      <NudgeController />

      <div className="flex flex-col lg:flex-row gap-6 items-start">

        {/* ── 좌측: 본문 읽기 영역 ── */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* 읽기 진행률 바 */}
          <ReadingProgressBar progress={progress} />

          {/* 본문 패널 */}
          <ReadingPane />

          {/* 완독 시: SessionSummaryCard 슬라이드업 등장 */}
          <SessionSummaryCard isVisible={isFinished} />

          {/* 완독 전: 안내 카드 */}
          {!isFinished && (
            <Card variant="flat" className="p-4 space-y-2">
              <p
                className="text-xs"
                style={{
                  color: 'var(--color-text-muted)',
                  fontFamily: 'var(--font-sans)',
                  lineHeight: 'var(--leading-normal)',
                }}
              >
                <span className="font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                  [6/26 Score Engine 작동 중]
                </span>{' '}
                스크롤할수록 Literacy Score가 실시간 계산됩니다. 25%/50%/75%/90%/완독 구간마다 대시보드 차트에 새 포인트가 추가됩니다.
                우측 패널 [집중도 시뮬]로 넛지→퀴즈 흐름을 시연하면, 퀴즈 결과도 즉시 점수에 반영됩니다.
              </p>
              <div 
                className="text-[11px] border-t border-dashed pt-2 mt-2 space-y-1"
                style={{
                  color: 'var(--color-text-muted)',
                  borderColor: 'var(--color-border)',
                  fontFamily: 'var(--font-sans)',
                  lineHeight: '1.4',
                }}
              >
                <span className="font-semibold block" style={{ color: 'var(--color-text-secondary)' }}>
                  ⚠️ 집중도(Focus Score) 측정의 조작적 정의 & 한계 명시
                </span>
                <p>
                  • 본 서비스에서의 <b>"집중"</b>이란 브라우저 활성화(Foreground) 상태, 개인 스크롤 baseline 기준 속도 준수, 단락 체류 안정성(2~20초)을 만족하는 독서 행동입니다.
                </p>
                <p>
                  • <b>측정 제한사항:</b> 창 이탈(Blur)은 전화 수신 등의 시스템 알림도 포함되어 감점될 수 있으며, 외부 단어 검색을 위한 이탈은 시스템이 의도를 인지하지 못해 이탈 감점 처리됩니다. (향후 인앱 단어 사전 완비로 보완 예정)
                </p>
              </div>
            </Card>
          )}
        </div>

        {/* ── 우측: 플로팅 제어판 ── */}
        <aside className="w-full lg:w-80 lg:shrink-0 lg:sticky lg:top-20 space-y-4">
          <FloatingControlPanel />
        </aside>

      </div>
    </div>
  );
}

/** 읽기 진행률 상단 바 */
function ReadingProgressBar({ progress }: { progress: number }) {
  const remainingMin = Math.max(0, Math.round((5 * (100 - progress)) / 100));

  return (
    <div
      className="rounded-lg border p-3 flex items-center gap-4"
      style={{
        backgroundColor: 'var(--color-surface)',
        borderColor: 'var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
          읽기 진행률
        </span>
        <span
          className="text-sm font-semibold tabular-nums"
          style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-sans)' }}
        >
          {progress}%
        </span>
      </div>
      <div
        className="flex-1 rounded-full h-2 overflow-hidden"
        style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${progress}%`,
            background: progress >= 100
              ? `linear-gradient(90deg, var(--color-engagement), var(--color-growth))`
              : `linear-gradient(90deg, var(--color-primary), var(--color-engagement))`,
            transition: 'width 0.5s ease',
          }}
        />
      </div>
      <span className="text-xs shrink-0" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
        {progress >= 100 ? '🎉 완독!' : `약 ${remainingMin}분 남음`}
      </span>
      {progress > 0 && (
        <Link
          to="/dashboard"
          className="shrink-0 text-xs px-2 py-1 rounded"
          style={{
            backgroundColor: 'var(--color-primary-tint)',
            color: 'var(--color-primary)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          📊 점수 보기
        </Link>
      )}
    </div>
  );
}
