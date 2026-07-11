/**
 * ExtensionPage — '/extension'
 * 크롬 확장 프로그램 설치 안내 페이지
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const STEPS = [
  {
    num: '시작 전에',
    icon: '🌐',
    title: '크롬(Chrome) 브라우저 필요',
    desc: '이 확장은 크롬에서만 동작해요. 엣지·사파리는 지원하지 않습니다.',
    highlight: false,
  },
  {
    num: '1단계',
    icon: '⬇️',
    title: '파일 내려받기',
    desc: '아래 [확장 프로그램 다운로드] 버튼을 눌러 압축파일(ai-literacy-care-extension.zip)을 받으세요.',
    highlight: false,
  },
  {
    num: '2단계',
    icon: '📦',
    title: '압축 풀기 (중요)',
    desc: '받은 파일을 압축 해제하세요.',
    note: '⚠️ 압축을 푼 폴더는 지우거나 옮기지 마세요. 확장이 이 폴더를 계속 참조해요.\n(예: 바탕화면/ai-literacy-care-extension)',
    highlight: true,
  },
  {
    num: '3단계',
    icon: '🔗',
    title: '확장 관리 페이지 열기',
    desc: '크롬 주소창에 chrome://extensions 를 입력하세요.',
    code: 'chrome://extensions',
    highlight: false,
  },
  {
    num: '4단계',
    icon: '🔧',
    title: '개발자 모드 켜기',
    desc: '화면 오른쪽 위 "개발자 모드" 스위치를 켜세요.',
    highlight: false,
  },
  {
    num: '5단계',
    icon: '📂',
    title: '폴더 불러오기',
    desc: '왼쪽 위 "압축해제된 확장 프로그램을 로드합니다" 클릭 → 2단계에서 압축 푼 폴더 안의 extension 폴더를 선택하세요.',
    note: '📖 AI 리터러시 케어 카드가 뜨면 설치 완료!',
    highlight: false,
  },
  {
    num: '6단계',
    icon: '🧩',
    title: '아이콘 고정 (선택)',
    desc: '주소창 오른쪽 퍼즐 조각(🧩) 아이콘 → AI툴바에 고정하면 편리해요.',
    highlight: false,
  },
  {
    num: '7단계',
    icon: '🚀',
    title: '사용 시작',
    desc: '읽고 싶은 웹페이지나 PDF를 열고, 툴바의 📖 아이콘 클릭 → 토글을 "켜짐"으로.\n이제 스크롤하며 읽으면 집중도가 측정돼요.',
    note: '(내 PDF 파일을 읽으려면 팝업의 "내 PDF 열기" 버튼을 누르세요.)',
    highlight: false,
  },
];

const FAQS = [
  {
    q: '"이 확장은 개발자 모드…" 경고가 떠요',
    a: '정상이에요. 개발자 모드로 설치해서 그래요. 그냥 닫으면 돼요.',
  },
  {
    q: '크롬을 껐다 켜니 확장이 사라졌어요',
    a: '2단계에서 압축 푼 폴더를 지웠는지 확인하세요. 폴더가 있어야 유지돼요.',
  },
  {
    q: '아이콘을 켰는데 반응이 없어요',
    a: '페이지를 새로고침(F5)해 보세요.',
  },
];

export default function ExtensionPage() {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = '확장 프로그램 설치 안내 — AI 리터러시 케어';
  }, []);

  // 확장 프로그램 zip 파일 다운로드
  // 실제 zip 파일이 public 폴더에 있다고 가정
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = '/ai-literacy-care-extension.zip';
    link.download = 'ai-literacy-care-extension.zip';
    link.click();
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg)',
        color: 'var(--color-text)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* 상단 헤더 */}
      <div
        style={{
          borderBottom: '1px solid var(--color-border)',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backgroundColor: 'var(--color-surface)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <button
          onClick={() => navigate('/home')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '13px',
            color: 'var(--color-text-secondary)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '6px 10px',
            borderRadius: 'var(--radius-sm)',
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--color-surface-alt)')}
          onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          ← 홈으로
        </button>
        <div
          style={{
            width: '1px',
            height: '16px',
            backgroundColor: 'var(--color-border)',
          }}
        />
        <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>확장 프로그램 설치</span>
      </div>

      <div style={{ maxWidth: '680px', margin: '0 auto', padding: '40px 24px 80px' }}>
        {/* 페이지 타이틀 */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 12px',
              backgroundColor: 'var(--color-primary-tint)',
              borderRadius: 'var(--radius-full)',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--color-primary)',
              marginBottom: '16px',
            }}
          >
            🧩 크롬 전용 · 2분 설치
          </div>
          <h1
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '28px',
              fontWeight: 700,
              lineHeight: 1.3,
              color: 'var(--color-text)',
              marginBottom: '10px',
              letterSpacing: 'var(--tracking-kr)',
            }}
          >
            크롬에서 읽기<br />— 확장 프로그램 설치
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', lineHeight: 1.7, marginBottom: '32px' }}>
            💡 이 확장은 크롬에서 읽는 글의 집중도를 측정해 도와줍니다.<br />
            아래 순서대로 한 번만 설치하면 돼요.
          </p>

          {/* 다운로드 버튼 (메인 CTA) */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleDownload}
            style={{
              width: '100%',
              padding: '16px 24px',
              backgroundColor: 'var(--color-primary)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius-lg)',
              fontSize: '16px',
              fontWeight: 700,
              fontFamily: 'var(--font-sans)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              boxShadow: '0 4px 20px rgba(200, 90, 50, 0.25)',
              marginBottom: '40px',
              letterSpacing: 'var(--tracking-kr)',
            }}
          >
            <span style={{ fontSize: '20px' }}>⬇️</span>
            확장 프로그램 다운로드
            <span style={{ fontSize: '12px', fontWeight: 400, opacity: 0.85 }}>ai-literacy-care-extension.zip</span>
          </motion.button>
        </motion.div>

        {/* 설치 단계 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '40px' }}>
          {STEPS.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: i * 0.05 }}
              style={{
                backgroundColor: step.highlight ? 'var(--color-nudge-medium-tint)' : 'var(--color-surface)',
                border: `1px solid ${step.highlight ? 'var(--color-nudge-medium)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                padding: '16px 20px',
                display: 'flex',
                gap: '16px',
                alignItems: 'flex-start',
              }}
            >
              {/* 스텝 번호 + 아이콘 */}
              <div
                style={{
                  flexShrink: 0,
                  width: '44px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '22px', lineHeight: 1 }}>{step.icon}</span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    color: step.highlight ? 'var(--color-nudge-medium)' : 'var(--color-primary)',
                    letterSpacing: '0.04em',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {step.num}
                </span>
              </div>

              {/* 내용 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p
                  style={{
                    fontSize: '14px',
                    fontWeight: 600,
                    color: 'var(--color-text)',
                    marginBottom: '4px',
                    letterSpacing: 'var(--tracking-kr)',
                  }}
                >
                  {step.title}
                </p>
                <p
                  style={{
                    fontSize: '13px',
                    color: 'var(--color-text-secondary)',
                    lineHeight: 1.65,
                    whiteSpace: 'pre-line',
                  }}
                >
                  {step.desc}
                </p>
                {step.code && (
                  <code
                    style={{
                      display: 'inline-block',
                      marginTop: '6px',
                      padding: '3px 10px',
                      backgroundColor: 'var(--color-surface-alt)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                      color: 'var(--color-primary)',
                      letterSpacing: '0.02em',
                    }}
                  >
                    {step.code}
                  </code>
                )}
                {step.note && (
                  <p
                    style={{
                      marginTop: '8px',
                      fontSize: '12px',
                      color: step.highlight ? 'var(--color-nudge-medium)' : 'var(--color-growth)',
                      lineHeight: 1.6,
                      whiteSpace: 'pre-line',
                      fontWeight: 500,
                    }}
                  >
                    {step.note}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* 자주 묻는 질문 */}
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '20px 24px',
            marginBottom: '32px',
          }}
        >
          <h2
            style={{
              fontSize: '14px',
              fontWeight: 700,
              color: 'var(--color-text)',
              marginBottom: '14px',
              letterSpacing: 'var(--tracking-kr)',
            }}
          >
            ❓ 자주 묻는 질문
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {FAQS.map((faq, i) => (
              <div key={i}>
                <p
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--color-text)',
                    marginBottom: '2px',
                  }}
                >
                  Q. {faq.q}
                </p>
                <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                  → {faq.a}
                </p>
                {i < FAQS.length - 1 && (
                  <div
                    style={{
                      height: '1px',
                      backgroundColor: 'var(--color-border)',
                      marginTop: '12px',
                    }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 하단 다운로드 버튼 반복 */}
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleDownload}
          style={{
            width: '100%',
            padding: '14px 24px',
            backgroundColor: 'var(--color-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-lg)',
            fontSize: '15px',
            fontWeight: 700,
            fontFamily: 'var(--font-sans)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            letterSpacing: 'var(--tracking-kr)',
          }}
        >
          ⬇️ 확장 프로그램 다운로드
        </motion.button>
      </div>
    </div>
  );
}
