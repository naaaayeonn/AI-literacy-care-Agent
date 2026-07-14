/**
 * SelectionLookup — 본문에서 임의의 단어/구를 드래그하면 뜻을 조회하는 위젯.
 * 기존 TermTooltip은 "미리 정한 용어"에만 hover 툴팁을 걸어서, 업로드한 글처럼
 * 사전에 없는 콘텐츠에서는 아무 단어도 조회할 수 없었다.
 * 이 컴포넌트는 사용자가 선택(드래그)한 어떤 단어든 백엔드 용어 조회(/api/terms/lookup)로 풀이한다.
 */
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { useReadingStore } from '../../stores/readingStore';

interface SelInfo {
  text: string;
  x: number;
  y: number;
  context: string;
}

export default function SelectionLookup() {
  const sessionId = useReadingStore((s) => s.sessionId);
  const termDefinitions = useReadingStore((s) => s.termDefinitions);
  const setTermDefinition = useReadingStore((s) => s.setTermDefinition);
  const enqueueEvent = useReadingStore((s) => s.enqueueEvent);

  const [sel, setSel] = useState<SelInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ text: string; found: boolean; source?: string } | null>(null);
  useEffect(() => {
    const onMouseUp = (e: MouseEvent) => {
      const targetEl = e.target as HTMLElement | null;
      const insideWidget = targetEl?.closest?.('[data-sellookup]');

      const s = window.getSelection();
      const text = s ? s.toString().replace(/\s+/g, ' ').trim() : '';

      // 선택이 없으면: 위젯 밖 클릭일 때만 닫는다 (칩/팝오버 클릭은 유지)
      if (!text) {
        if (!insideWidget) {
          setSel(null);
          setResult(null);
        }
        return;
      }

      // 너무 길거나 짧은 선택은 무시 (단어/짧은 구만)
      if (text.length < 1 || text.length > 40) return;

      // 본문(.reading) 안에서의 선택만 대상으로
      const anchor = s!.anchorNode as Node | null;
      const el =
        anchor && (anchor.nodeType === 3 ? anchor.parentElement : (anchor as HTMLElement));
      const readingRoot = el && el.closest ? el.closest('.reading') : null;
      if (!readingRoot) return;

      const rect = s!.getRangeAt(0).getBoundingClientRect();
      const paraEl = el && el.closest ? (el.closest('[data-paragraph]') as HTMLElement | null) : null;
      const context = paraEl?.innerText?.slice(0, 300) ?? '';

      setSel({ text, x: rect.left + rect.width / 2, y: rect.top, context });
      setResult(null);
    };

    document.addEventListener('mouseup', onMouseUp as EventListener);
    document.addEventListener('touchend', onMouseUp as EventListener);
    return () => {
      document.removeEventListener('mouseup', onMouseUp as EventListener);
      document.removeEventListener('touchend', onMouseUp as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!sel) return;

    const runLookup = async () => {
      const cached = termDefinitions[sel.text];
      if (cached) {
        setResult({ text: cached, found: true });
        enqueueEvent({
          type: 'lookup',
          sessionId: sessionId || '',
          timestamp: Date.now(),
          timestamp_ms: Date.now(),
          payload: {
            term: sel.text,
            definition: cached,
            status: 'review',
          },
        });
        return;
      }

      setLoading(true);
      try {
        const res = await api.getTermDefinition(sessionId || '', sel.text, sel.context);
        
        // RAG에 없거나 에러가 나더라도, 사용자가 드래그해서 뜻을 알려고 했던 의도가 있으므로 
        // 무조건 이벤트를 등록하여 단어장에 적재되게 한다.
        const explanation = (res.explanation && res.source !== 'not_found') 
          ? res.explanation 
          : `'${sel.text}'에 대한 사전 뜻을 임시로 조회하지 못했습니다. (배포 시 국어사전 API 키를 연결하면 실시간 풀이가 제공됩니다)`;
        
        setResult({ text: explanation, found: true, source: res.source });
        setTermDefinition(sel.text, explanation);
        
        enqueueEvent({
          type: 'lookup',
          sessionId: sessionId || '',
          timestamp: Date.now(),
          timestamp_ms: Date.now(),
          payload: {
            term: sel.text,
            definition: explanation,
            status: 'review',
          },
        });
      } catch {
        const fallbackMsg = '설명을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.';
        setResult({ text: fallbackMsg, found: false });
      } finally {
        setLoading(false);
      }
    };

    runLookup();
  }, [sel, sessionId, termDefinitions, setTermDefinition, enqueueEvent]);

  if (!sel) return null;

  const popTop = Math.max(8, sel.y - 12);

  return (
    <div data-sellookup>
      <div
        style={{
          position: 'fixed',
          left: sel.x,
          top: popTop,
          transform: 'translate(-50%, -100%)',
          zIndex: 60,
          width: 260,
          backgroundColor: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md, 10px)',
          boxShadow: 'var(--shadow-panel, 0 8px 30px rgba(0,0,0,0.18))',
          padding: '12px 14px',
          fontFamily: 'var(--font-sans)',
        }}
      >
        <div style={{ fontWeight: 700, color: 'var(--color-text)', marginBottom: 6 }}>
          {sel.text}
        </div>
        <div
          style={{
            fontSize: 12,
            color: result?.found === false ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
            lineHeight: 1.5,
            minHeight: 18,
          }}
        >
          {loading ? '⏳ AI가 뜻을 찾는 중…' : result?.text}
        </div>
        {result?.found && result?.source && (
          <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textAlign: 'right', marginTop: 4 }}>
            [출처] {result.source}
          </div>
        )}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: 10,
          }}
        >
          <span style={{ fontSize: 9, fontWeight: 600, color: 'var(--color-text-muted)' }}>
            📖 AI 리터러시 케어 용어 조회
          </span>
          <button
            onClick={() => {
              setSel(null);
              setResult(null);
              window.getSelection()?.removeAllRanges();
            }}
            style={{
              fontSize: 11,
              color: 'var(--color-primary)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
