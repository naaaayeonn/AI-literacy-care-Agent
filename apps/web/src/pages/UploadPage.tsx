/**
 * UploadPage — '/upload'
 * 7/11 고도화: 내 문서 보관함 (목록 조회) 및 신규 문서 업로드 폼 통합 제공.
 * 여태껏 업로드한 파일 리스트를 로컬스토리지에 저장하여 마주 읽기 기능을 지원합니다.
 */
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionConfig } from '../stores/sessionConfigStore';
import { useReadingStore } from '../stores/readingStore';
import { Button } from '../components/common/Button';
import BottomTabBar from '../components/common/BottomTabBar';

interface UploadedArticle {
  id: string;
  title: string;
  content: string[];
  category: string;
  author: string;
  uploadedAt: string;
}

const SAMPLE_TEXTS = [
  "인공지능 기술이 일상에 빠르게 스며들면서, 정보를 비판적으로 읽는 능력의 중요성이 커지고 있습니다.",
  "특히 대규모 언어 모델이 만들어내는 그럴듯한 문장은 사실과 허구를 구분하기 어렵게 만듭니다. 따라서 출처를 확인하고 맥락을 따지는 습관이 필요합니다.",
  "이 글을 통해 실제로 집중도를 측정하고 필요한 순간에 제공되는 실시간 문맥 퀴즈 개입 시스템을 생생하게 체험하실 수 있습니다."
];

// 기본 제공되는 디지털 리터러시 관련 고품질 데모 기사 목록
const DEFAULT_DEMO_ARTICLES: UploadedArticle[] = [
  {
    id: 'demo-ax',
    title: '🤖 인공지능 전환(AX)과 디지털 리터러시의 사회학',
    content: [
      "인공지능 전환(AX)이 가속화되면서 인간이 정보를 해석하고 재생산하는 방식에 혁명적 변화가 일어나고 있습니다. 과거의 디지털 격차가 '기기를 다룰 수 있는가'의 문제였다면, 현재의 격차는 'AI가 쏟아내는 정보의 진위를 비판적으로 성찰할 수 있는가'로 고도화되었습니다.",
      "대규모 언어 모델(LLM)이 작성한 텍스트는 겉보기에 완벽한 문장 구조를 지녀 독자를 쉽게 현혹합니다. 이를 무비판적으로 소비할 경우 인지부하를 외부 AI에 전적으로 외주화하게 되어, 인간 고유의 심층 독해 능력이 저하되는 인지적 Offloading 현상이 가속화됩니다.",
      "따라서 AI 시대의 리터러시는 단순한 텍스트 해독이 아닌 텍스트의 맥락적 추론, 출처 교차 검증, 그리고 자신의 사고 과정을 스스로 통제하는 메타인지적 집중력이 중심이 되어야 합니다. AllDayHappyDay는 이러한 인지 체력을 단단히 방어하기 위해 설계되었습니다."
    ],
    category: 'IT/사회',
    author: 'AI 교육연구소',
    uploadedAt: new Date(Date.now() - 3600000 * 24).toISOString() // 1일 전
  },
  {
    id: 'demo-physics',
    title: '📘 뢴트겐의 X-선 스펙트럼과 금속의 결정 구조 분석',
    content: [
      "뢴트겐에 의해 발견된 X-선은 0.01~10nm 범위의 파장을 갖는 전자기파로, 가시광선의 파장에 비해 매우 짧아 물체에 깊숙이 침투하고 투과할 수 있는 특징을 지닙니다. 이는 재료의 표면뿐만 아니라 보이지 않는 내부 결정을 파악하는 데 널리 활용됩니다.",
      "X-선은 진공 속 전극 사이에 고전압을 가해 금속 필라멘트에서 방출된 열전자가 양극의 금속 표적을 큰 운동에너지로 충돌할 때 발생합니다. 방출된 X-선의 파장과 세기를 기록하면 Kα와 Kβ 등 뾰족하게 솟은 고유한 특성 스펙트럼 봉우리를 관찰할 수 있습니다.",
      "금속은 원자가 층층이 규칙적으로 쌓여 있는 결정 구조를 가집니다. 특정 각도로 입사된 X-선이 각 원자층에서 반사되어 나올 때, 파동의 위상차에 따라 보강간섭과 상쇄간섭을 일으킵니다. 이 간섭 무늬를 역추적하면 금속의 정교한 3차원 결정 구조를 원자 수준에서 완벽하게 밝혀낼 수 있습니다."
    ],
    category: '기초과학',
    author: '2026학년도 수능특강',
    uploadedAt: new Date(Date.now() - 3600000 * 12).toISOString() // 12시간 전
  }
];

const ARTICLES_KEY = 'local_uploaded_articles_db';

export default function UploadPage() {
  const navigate = useNavigate();

  const setUpload = useSessionConfig((s) => s.setUpload);
  const setArticle = useReadingStore((s) => s.setArticle);

  // 화면 모드: 'list' (보관함 목록) | 'create' (문서 등록 양식)
  const [viewMode, setViewMode] = useState<'list' | 'create'>('list');
  const [articles, setArticles] = useState<UploadedArticle[]>([]);

  // 신규 등록용 State
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [error, setError] = useState('');
  const [parsingPdf, setParsingPdf] = useState(false);

  // PDF 파일 → pdf.js로 문단 추출(확장 뷰어와 동일 로직, 번들·오프라인 안전) → 본문 자동 입력.
  // pdf.js는 크므로 실제 업로드 시에만 지연 로딩한다.
  const processPdf = async (file: File | undefined | null) => {
    if (!file) return;
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('PDF 파일만 올릴 수 있어요.');
      return;
    }
    if (!title.trim()) setTitle(file.name.replace(/\.pdf$/i, ''));
    setParsingPdf(true);
    setError('');
    try {
      const { extractPdfParagraphs } = await import('../lib/pdfExtract');
      const paras = await extractPdfParagraphs(file);
      if (paras.length === 0) {
        setError('PDF에서 텍스트를 추출하지 못했어요. 스캔한 이미지 PDF는 글자 레이어가 없을 수 있어요.');
      } else {
        setBody(paras.join('\n\n'));
      }
    } catch (err) {
      console.error('[PDF] 추출 실패:', err);
      setError('PDF를 읽는 중 오류가 발생했어요. 다른 파일로 시도해 주세요.');
    } finally {
      setParsingPdf(false);
    }
  };

  // 1. 로컬스토리지에서 업로드된 문서 목록 로드 (없으면 데모 주입)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(ARTICLES_KEY);
      if (raw) {
        setArticles(JSON.parse(raw));
      } else {
        localStorage.setItem(ARTICLES_KEY, JSON.stringify(DEFAULT_DEMO_ARTICLES));
        setArticles(DEFAULT_DEMO_ARTICLES);
      }
    } catch {
      setArticles(DEFAULT_DEMO_ARTICLES);
    }
  }, []);

  const paragraphs = useMemo(
    () =>
      body
        .split(/\n\s*\n/)
        .map((p) => p.replace(/\s+/g, ' ').trim())
        .filter((p) => p.length > 0),
    [body]
  );

  const charCount = body.replace(/\s/g, '').length;

  // 신규 문서 등록 및 마저 읽기 시작
  const handleStart = () => {
    if (paragraphs.length === 0 || charCount < 20) {
      setError('본문을 20자 이상 붙여넣어 주세요.');
      return;
    }
    const finalTitle = title.trim() || '내가 올린 문서';
    
    const newArticle: UploadedArticle = {
      id: 'art_' + Math.random().toString(36).substr(2, 9),
      title: finalTitle,
      content: paragraphs,
      category: '내 업로드',
      author: '익명 업로드',
      uploadedAt: new Date().toISOString()
    };

    const updated = [newArticle, ...articles];
    setArticles(updated);
    try {
      localStorage.setItem(ARTICLES_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error(e);
    }

    // 세션 기동 데이터 셋업
    setUpload(newArticle.title, newArticle.content);
    setArticle({
      id: newArticle.id,
      title: newArticle.title,
      category: newArticle.category,
      author: newArticle.author,
      publishedAt: '방금',
      content: newArticle.content,
    });
    
    navigate('/reading');
  };

  // 기존 기사 클릭 시 독서 시작
  const handleSelectArticle = (art: UploadedArticle) => {
    setUpload(art.title, art.content);
    setArticle({
      id: art.id,
      title: art.title,
      category: art.category,
      author: art.author,
      publishedAt: '보관함 문서',
      content: art.content,
    });
    navigate('/reading');
  };

  return (
    <div
      className="min-h-screen px-4 pt-10 pb-28"
      style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
    >
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/home')}
          className="text-sm mb-4 cursor-pointer hover:underline"
          style={{ color: 'var(--color-text-muted)' }}
        >
          ← 홈으로 돌아가기
        </button>

        {viewMode === 'list' ? (
          /* ── 리스트 뷰: 내 문서 보관함 ── */
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold mb-1" style={{ letterSpacing: 'var(--tracking-kr)' }}>
                  📄 내 문서 보관함
                </h1>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  여태껏 등록한 파일 목록입니다. 읽고 싶은 글을 클릭해 실시간 케어를 진행해 보세요.
                </p>
              </div>
              
              <Button 
                variant="primary" 
                size="md" 
                onClick={() => {
                  setViewMode('create');
                  setTitle('');
                  setBody('');
                  setError('');
                }}
              >
                파일 업로드 ＋
              </Button>
            </div>

            {articles.length === 0 ? (
              <div 
                className="rounded-xl border p-12 text-center"
                style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
              >
                <div className="text-4xl mb-3">📁</div>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>보관함이 비어 있습니다. 새 문서를 먼저 등록해 보세요!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {articles.map((art) => (
                  <div
                    key={art.id}
                    onClick={() => handleSelectArticle(art)}
                    className="rounded-xl border p-4 flex justify-between items-center transition-all duration-200 hover:-translate-y-0.5 cursor-pointer hover:shadow-sm"
                    style={{
                      backgroundColor: 'var(--color-surface)',
                      borderColor: 'var(--color-border)'
                    }}
                  >
                    <div className="space-y-1 pr-4 flex-1">
                      <div className="font-semibold text-sm line-clamp-1" style={{ color: 'var(--color-text)' }}>
                        {art.title}
                      </div>
                      <div className="flex items-center gap-2 text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>
                        <span>📂 {art.category}</span>
                        <span>•</span>
                        <span>📝 {art.content.length}개 단락</span>
                        <span>•</span>
                        <span className="tabular-nums">⏰ {new Date(art.uploadedAt).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="shrink-0 text-xs font-semibold" style={{ color: 'var(--color-primary)' }}>
                      마저 읽기 →
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* ── 작성 뷰: 새 문서 업로드 폼 ── */
          <div className="space-y-6">
            <div>
              <button
                onClick={() => setViewMode('list')}
                className="text-xs mb-2 cursor-pointer hover:underline"
                style={{ color: 'var(--color-primary)' }}
              >
                ← 내 보관함 목록으로 가기
              </button>
              <h1 className="text-2xl font-bold mb-1" style={{ letterSpacing: 'var(--tracking-kr)' }}>
                📄 새 문서 등록하기
              </h1>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                아티클의 텍스트 본문을 등록하면 분석 알고리즘이 적용된 인앱 뷰어로 독서가 시작됩니다.
              </p>
            </div>

            {/* 7/11: 크롬 확장 설치 안내는 전용 /extension 페이지로 위임하고 이곳은 숨김 처리 */}

            <div className="space-y-4">
              {/* PDF 파일 드롭 영역 */}
              <div
                className="border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 hover:opacity-90"
                style={{
                  borderColor: parsingPdf ? 'var(--color-primary)' : 'var(--color-border)',
                  backgroundColor: 'var(--color-surface-alt)',
                }}
                onClick={() => !parsingPdf && document.getElementById('pdf-file-input')?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => { e.preventDefault(); if (!parsingPdf) void processPdf(e.dataTransfer.files?.[0]); }}
              >
                <div className="text-3xl mb-1">{parsingPdf ? '⚙️' : '📁'}</div>
                <div className="text-sm font-bold">
                  {parsingPdf ? 'PDF 본문 텍스트 분석 중...' : 'PDF 파일 올리기'}
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                  {parsingPdf
                    ? '잠시만 기다려 주세요. 텍스트를 파싱 중입니다.'
                    : 'PDF를 끌어다 놓거나 클릭해서 첨부하면 본문이 아래 폼에 자동 입력됩니다. (파일은 서버로 올라가지 않아요)'}
                </p>
                <input
                  id="pdf-file-input"
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => void processPdf(e.target.files?.[0])}
                  disabled={parsingPdf}
                  className="hidden"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1">제목 (선택)</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="예: 인공지능 전환(AX)과 읽기 능력의 변화"
                  className="w-full rounded-md border px-3 py-2 text-sm outline-none"
                  style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-semibold">본문 <span style={{ color: 'var(--color-danger)' }}>*</span></label>
                  <button
                    onClick={() => { setBody(SAMPLE_TEXTS.join('\n\n')); setError(''); }}
                    className="text-xs underline cursor-pointer"
                    style={{ color: 'var(--color-primary)' }}
                  >
                    샘플 텍스트로 채우기
                  </button>
                </div>
                <textarea
                  value={body}
                  onChange={(e) => { setBody(e.target.value); if (error) setError(''); }}
                  placeholder="여기에 읽을 본문을 붙여넣으세요. (엔터 두 번을 쳐서 빈 줄을 두면 다른 단락으로 나뉩니다.)"
                  rows={12}
                  className="w-full rounded-md border px-3 py-2 text-sm outline-none resize-y"
                  style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text)', lineHeight: 'var(--leading-normal)' }}
                />
              </div>

              <div className="flex items-center justify-between text-xs" style={{ color: 'var(--color-text-muted)' }}>
                <span>{paragraphs.length}개 단락 · {charCount}자</span>
                {error && <span style={{ color: 'var(--color-danger)' }}>{error}</span>}
              </div>

              <Button variant="primary" size="lg" className="w-full" onClick={handleStart}>
                등록하고 바로 읽기 시작 →
              </Button>
            </div>
          </div>
        )}
      </div>
      
      {/* 7/11: 하단 고정 탭 네비게이션 바 */}
      <BottomTabBar />
    </div>
  );
}
