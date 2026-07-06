/**
 * ReadingPane — 6/23 실구현
 *
 * [구현된 기능]
 * - sampleArticle mock 데이터 렌더링 (.reading 유틸 클래스)
 * - 스크롤 위치 기반 진행률 실시간 계산 → readingStore.setProgress()
 * - 탭 blur/focus 이벤트 → gazeOutCount 누적
 * - 단락 체류 시간 측정 (IntersectionObserver)
 * - highlightedParagraphs 인덱스에 해당하는 단락에 HighlightText 적용
 * - 핵심 용어에 TermTooltip 적용 (sampleTerms 기준)
 *
 * TODO 6/24: focusStore.nudgeLevel 변화 → Nudge 컴포넌트 조건부 렌더
 * TODO 6/30: ②번 RAG 용어 정의 API 연결
 */
import React, { useEffect, useRef, useCallback } from 'react';
import { sampleArticle } from '../../mock/sampleArticle';
import { useReadingStore } from '../../stores/readingStore';
import HighlightText from './HighlightText';
import TermTooltip from './TermTooltip';
import {
  getActiveWsClient,
  sendScrollEvent,
  sendDwellEvent,
  sendBlurEvent,
  sendFocusEvent,
} from '../../lib/ws';

// ── 핵심 용어 사전 (6/30: ②번 RAG로 교체) ──────────────────────────
const TERM_DICT: Record<string, string> = {
  '디지털 리터러시': '디지털 환경에서 정보를 읽고, 평가하고, 활용하는 복합적 역량.',
  'LLM': '대규모 언어 모델(Large Language Model). GPT, Claude 등이 해당되며, 방대한 텍스트 데이터로 훈련된 AI.',
  '환각 현상': 'AI가 그럴듯하지만 사실이 아닌 정보를 생성하는 현상. Hallucination이라고도 함.',
  '인지부하': '특정 작업을 처리할 때 뇌에 가해지는 정신적 부담의 정도.',
  '넛지': '강제 없이 부드러운 방식으로 특정 행동을 유도하는 개입 기법.',
  'Literacy Score': '본 서비스의 핵심 지표. 이해도·집중도·난이도 보정을 합산한 문해력 점수.',
};

/** 단락 텍스트에서 용어 사전의 키워드를 찾아 TermTooltip으로 감싼 JSX 배열 반환 */
function renderWithTerms(text: string): React.ReactNode[] {
  const terms = Object.keys(TERM_DICT);
  // 모든 용어를 하나의 정규식으로 매칭
  const pattern = new RegExp(`(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g');
  const parts = text.split(pattern);

  return parts.map((part, i) => {
    if (TERM_DICT[part]) {
      return (
        <TermTooltip key={i} term={part} definition={TERM_DICT[part]}>
          {part}
        </TermTooltip>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

// ── 단락 컴포넌트 ────────────────────────────────────────────────────
interface ParagraphProps {
  index: number;
  text: string;
  isHighlighted: boolean;
  onVisible: (index: number) => void;
}

const Paragraph: React.FC<ParagraphProps> = React.memo(({ index, text, isHighlighted, onVisible }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) onVisible(index);
      },
      { threshold: 0.5 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [index, onVisible]);

  const content = renderWithTerms(text);

  return (
    <div
      ref={ref}
      data-paragraph={index}
      style={{
        textAlign: 'justify',
        marginBottom: 'var(--space-6)',
        position: 'relative',
        padding: '6px 10px',
        borderLeft: `3px solid ${isHighlighted ? 'var(--color-primary)' : 'transparent'}`,
        borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
        backgroundColor: isHighlighted ? 'var(--color-primary-tint)' : 'transparent',
        transition: 'background-color 0.4s ease, border-left 0.4s ease',
      }}
    >
      {isHighlighted ? <HighlightText intensity="normal">{content}</HighlightText> : content}
    </div>
  );
});
Paragraph.displayName = 'Paragraph';

// ── ReadingPane ───────────────────────────────────────────────────────
export const ReadingPane: React.FC = () => {
  const {
    setProgress,
    setScrollVelocity,
    incrementGazeOut,
    setDwellTime,
    highlightedParagraphs,
    sessionId,
    showGlossesInline,
    toggleGlossesInline,
  } = useReadingStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const lastScrollY = useRef(0);
  const lastScrollTime = useRef(Date.now());
  const dwellStart = useRef(Date.now());
  const currentParagraph = useRef(0);

  // ── 스크롤 진행률 + 속도 계산 ──
  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    const scrollTop = el.scrollTop;
    const scrollHeight = el.scrollHeight - el.clientHeight;
    const progress = scrollHeight > 0 ? Math.round((scrollTop / scrollHeight) * 100) : 0;
    const clampedProgress = Math.min(100, Math.max(0, progress));
    setProgress(clampedProgress);

    const now = Date.now();
    const deltaY = Math.abs(scrollTop - lastScrollY.current);
    const deltaT = (now - lastScrollTime.current) / 1000; // seconds
    const velocity = deltaT > 0 ? Math.round(deltaY / deltaT) : 0;
    setScrollVelocity(velocity);

    // ── 7/6 WebSocket 전송 ──
    const wsClient = getActiveWsClient();
    if (wsClient && sessionId) {
      sendScrollEvent(wsClient, sessionId, velocity, clampedProgress);
    }

    lastScrollY.current = scrollTop;
    lastScrollTime.current = now;
  }, [setProgress, setScrollVelocity, sessionId]);

  // ── 탭 포커스 이탈 감지 ──
  useEffect(() => {
    const onBlur = () => {
      incrementGazeOut();
      const wsClient = getActiveWsClient();
      if (wsClient && sessionId) sendBlurEvent(wsClient, sessionId);
    };
    const onFocus = () => {
      const wsClient = getActiveWsClient();
      if (wsClient && sessionId) sendFocusEvent(wsClient, sessionId);
    };
    window.addEventListener('blur', onBlur);
    window.addEventListener('focus', onFocus);
    return () => {
      window.removeEventListener('blur', onBlur);
      window.removeEventListener('focus', onFocus);
    };
  }, [incrementGazeOut, sessionId]);

  // ── 단락 체류 시간 누적 ──
  const handleParagraphVisible = useCallback(
    (index: number) => {
      if (index !== currentParagraph.current) {
        const elapsed = Date.now() - dwellStart.current;
        setDwellTime(elapsed);

        // ── 7/6 WebSocket 전송 ──
        const wsClient = getActiveWsClient();
        if (wsClient && sessionId) {
          sendDwellEvent(wsClient, sessionId, String(currentParagraph.current), elapsed);
        }

        dwellStart.current = Date.now();
        currentParagraph.current = index;
      }
    },
    [setDwellTime, sessionId]
  );

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden',
      }}
    >
      {/* 기사 메타 헤더 */}
      <div style={{ padding: 'var(--space-6) var(--space-8) var(--space-4)' }}>
        <div style={{ marginBottom: 'var(--space-3)' }}>
          <span
            style={{
              display: 'inline-block',
              padding: '2px 10px',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--weight-semibold)' as unknown as number,
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--color-primary-tint)',
              color: 'var(--color-primary)',
              fontFamily: 'var(--font-sans)',
              marginBottom: 'var(--space-2)',
            }}
          >
            {sampleArticle.category}
          </span>
          <h1
            style={{
              fontSize: 'var(--text-2xl)',
              fontWeight: 'var(--weight-bold)' as unknown as number,
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
              lineHeight: 'var(--leading-tight)',
              letterSpacing: 'var(--tracking-kr)',
              marginBottom: 'var(--space-2)',
            }}
          >
            {sampleArticle.title}
          </h1>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 'var(--space-2)',
            }}
          >
            <p
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--color-text-secondary)',
                fontFamily: 'var(--font-sans)',
                margin: 0,
              }}
            >
              저자: {sampleArticle.author} · 발행일: {sampleArticle.publishedAt}
            </p>
            <button
              onClick={toggleGlossesInline}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '12px',
                fontWeight: 600,
                color: showGlossesInline ? 'white' : 'var(--color-primary)',
                backgroundColor: showGlossesInline ? 'var(--color-primary)' : 'var(--color-primary-tint)',
                border: '1px solid var(--color-primary)',
                borderRadius: 'var(--radius-full)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                outline: 'none',
                fontFamily: 'var(--font-sans)',
              }}
              onMouseEnter={(e) => {
                if (!showGlossesInline) {
                  e.currentTarget.style.backgroundColor = 'rgba(130, 87, 230, 0.2)';
                }
              }}
              onMouseLeave={(e) => {
                if (!showGlossesInline) {
                  e.currentTarget.style.backgroundColor = 'var(--color-primary-tint)';
                }
              }}
            >
              <span>{showGlossesInline ? '📖 RAG AI 주석 상시 표시 중' : '💡 RAG AI 주석 상시 표시'}</span>
            </button>
          </div>
        </div>
        <hr style={{ borderColor: 'var(--color-border)', margin: '0' }} />
      </div>

      {/* 스크롤 가능한 본문 영역 */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        style={{
          padding: '0 var(--space-8) var(--space-8)',
          maxHeight: '65vh',
          overflowY: 'auto',
          // 스크롤바 스타일링
          scrollbarWidth: 'thin',
          scrollbarColor: 'var(--color-border) transparent',
        }}
      >
        {/* .reading 유틸 클래스: 68ch × leading-reading × text-reading */}
        <div
          className="reading"
          style={{
            marginInline: 'auto',
            paddingTop: 'var(--space-6)',
            fontFamily: 'var(--font-sans)',
            color: 'var(--color-text)',
            letterSpacing: 'var(--tracking-kr)',
          }}
        >
          {sampleArticle.content.map((paragraph, index) => (
            <Paragraph
              key={index}
              index={index}
              text={paragraph}
              isHighlighted={highlightedParagraphs.includes(index)}
              onVisible={handleParagraphVisible}
            />
          ))}

          {/* 완독 시 표시 */}
          <div
            style={{
              textAlign: 'center',
              padding: 'var(--space-6)',
              borderTop: '1px solid var(--color-border)',
              color: 'var(--color-text-muted)',
              fontSize: 'var(--text-xs)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            🎉 읽기 감지 영역 · 스크롤 진행률 및 단락 체류 시간이 실시간 측정됩니다
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReadingPane;
