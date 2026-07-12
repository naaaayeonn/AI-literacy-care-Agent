import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, User, ClipboardList, Timer, Lightbulb, Rocket, Book, BookOpen, Flag, BarChart2, AlertCircle, Target, CheckCircle2 } from 'lucide-react';
import { useSessionConfig } from '../stores/sessionConfigStore';
import { Button } from '../components/common/Button';
import { useAuthStore } from '../stores/authStore';
import TutorialModal from '../components/common/TutorialModal';

// 캘리브레이션 텍스트 정의
const EASY_TEXTS = [
  "인간과 동물의 가장 큰 차이점 중 하나는 바로 불을 다루는 능력입니다. 인류의 조상들은 우연한 기회에 자연적으로 발생한 불을 발견하였고, 이를 보존하고 활용하는 방법을 터득하게 되었습니다. 불은 밤의 어둠을 밝혀주었을 뿐만 아니라, 맹수들의 위협으로부터 인간을 보호하는 강력한 무기가 되었습니다.",
  "또한 불을 이용하여 음식을 익혀 먹음으로써 소화 효율을 높이고 질병을 예방할 수 있게 되었으며, 이는 인류의 뇌 용량이 극적으로 증가하고 신체가 진화하는 데 결정적인 기여를 하였습니다. 나아가 인류는 추운 겨울에도 따뜻함을 유지하며 척박한 환경에 적응할 수 있는 생존의 발판을 마련하게 되었습니다.",
  "역사적으로 인류는 불을 통제하는 능력을 더욱 발전시켜 금속을 제련하고 도구를 제작하는 기술적 도약을 이룩하였습니다. 흙을 구워 단단한 토기를 만들고 광석에서 구리와 철을 추출해 내는 과정은 모두 불의 세밀한 제어가 있었기에 가능했습니다. 이는 수렵 채집 사회를 넘어 농경과 정착 생활을 가능케 한 문명 발전의 원동력이 되었습니다.",
  "현대에 이르러서도 불은 다양한 형태의 에너지원으로 변환되어 우리의 일상을 지탱하고 있습니다. 발전소에서 화석 연료를 태워 전기를 생산하고, 자동차 엔진 속에서 연료를 폭발시켜 바퀴를 굴리는 등 현대 과학 기술 문명의 기초는 불의 활용에서 비롯되었습니다. 결국 불은 인류 문명의 시작과 끝을 함께하는 가장 위대한 도구라고 할 수 있습니다."
];

const HARD_TEXTS = [
  "뢴트겐에 의해 발견된 X-선은 0.01~10nm 범위의 파장을 갖는 전자기파로, 가시광선의 파장이 수백 nm 정도인 것에 비해 매우 짧은 파장을 갖는다. 전자기파의 에너지는 파장이 짧을수록 더 큰 에너지를 가지기 때문에 물체에 깊숙이 침투할 수 있으며 물체를 투과할 수도 있다. X-선은 파장이 매우 짧아 재료의 표면뿐만 아니라 내부의 정보를 분석할 때 널리 쓰인다.",
  "그렇다면 X-선은 어떻게 발생시킬 수 있을까? 진공 내에 설치된 양극과 음극 사이에 수십 kV의 고전압을 가하면 음극의 금속 필라멘트가 가열된다. 금속이 가열되면 금속 표면으로부터 전자가 튀어나오게 되는데, 이를 열전자 방출이라 한다. 이 현상으로 금속 필라멘트에서 튀어나온 전자는 양극과 음극 사이에 걸려 있는 전압에 의해 양극 쪽으로 가속된다. 그리고 그 전자가 큰 운동 에너지를 유지한 채 양극의 금속 표적을 때리면 X-선이 방출된다. 그러나 가속된 전자의 운동 에너지 대부분은 열에너지로 전환되어 금속 표적 온도가 올라가게 되므로 금속 표적이 녹지 않도록 금속 표적을 냉각해야 한다.",
  "방출된 X-선에 대해 가로축에 파장, 세로축에 세기를 나타내는 그래프를 그리면 연속적으로 이어진 선을 얻을 수 있는데 이를 X-선 스펙트럼이라 한다. X-선 스펙트럼에는 바늘 모양으로 뾰족하게 튀어나와 있는 두 봉우리가 관찰되며 이 두 봉우리를 각각 Kα와 Kβ로 부른다. 금속의 한 종류인 몰리브덴의 경우 0.05에서 0.25nm 사이의 X-선이 방출되며, Kα와 Kβ는 각각 0.07nm와 0.06nm이다. 이렇게 Kα와 Kβ와 같은 특성 스펙트럼이 나타나는 이유는 금속의 원자에 속박된 전자들이 차지할 수 있는 안정된 에너지 준위가 불연속적이기 때문이다. 금속의 원자에 속박된 전자는 K, L, M, N의 불연속적인 특정한 에너지 준위를 갖는다. K의 에너지를 갖는 전자가 가속된 전자에 부딪혀 튕겨 나가면 L이나 M과 같이 더 높은 준위에 있던 전자 중 일부가 낮은 에너지 준위의 K로 떨어지면서 그 차이에 해당하는 특정 파장의 에너지를 방출한다. 이러한 특성 스펙트럼은 K, L, M, N과 같은 전자의 에너지 준위가 금속의 종류에 따라 다르므로, 표적 물질로 쓰인 금속의 종류에 따라 L에 있던 전자가 K로 떨어지면서 방출되는 Kα와 M에 있던 전자가 K로 떨어지면서 방출되는 Kβ가 각각 고유한 값을 갖는다.",
  "전자기파 필터를 이용하면 발생된 X-선으로부터 특정 파장을 갖는 단파장의 X-선을 얻을 수 있는데 이러한 단파장을 이용하면 금속의 결정 구조를 파악할 수 있다. 금속은 결정 구조를 갖는데 결정은 원자가 층층이 규칙적으로 쌓여 있는 구조이다. 각 층은 X-선을 반사하는 거울과 같은 역할을 한다. 따라서 금속의 표면에 특정 각도로 입사된 X-선은 표면에서 일부는 바로 반사되고 일부는 표면 아래층에서 반사되어 나온다. 이때 표면에서 반사된 X-선과 표면 아래층에서 반사되어 나온 X-선은 상호 작용을 한다. 이러한 상호 작용으로 나타나는 것이 보강간섭과 상쇄간섭인데, 보강간섭은 파동이 같은 위상으로 중첩되어 진폭이 커지는 현상이며 상쇄간섭은 파동이 반대 위상으로 중첩되어 진폭이 작아지는 간섭을 말한다. X-선은 전자기파이기 때문에 마루와 골을 갖는 사인 함수 모양이므로, 아래층에서 반사되어 나온 X-선의 마루와 골이 표면에서 반사된 X-선의 마루와 골과 위상차가 발생하지 않으면 반사된 X-선은 보강간섭이 최대로 생기게 된다. 즉 표면을 투과하여 아래의 원자층에 의해 반사되어 나오는 X-선의 경로와 바로 표면에서 반사한다."
];

type Step = 'consent' | 'intro' | 'calibration_easy' | 'calibration_hard' | 'result';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const onboard = useSessionConfig((s) => s.onboard);
  
  // 7/11: 로컬 인증 및 온보딩 세션 구독
  const { user, isAuthenticated } = useAuthStore();
  const setBaseline = useSessionConfig((s) => s.setBaseline);
  
  const [step, setStep] = useState<Step>('consent');
  const [agreed, setAgreed] = useState(false);

  // 캘리브레이션 측정용 상태
  const [scrollVelocities, setScrollVelocities] = useState<number[]>([]);
  const [currentVelocity, setCurrentVelocity] = useState(0);
  const [easyBaseline, setEasyBaseline] = useState<number | null>(null);
  const [hardBaseline, setHardBaseline] = useState<number | null>(null);

  const lastScrollY = useRef(0);
  const lastScrollTime = useRef(Date.now());
  const velocityTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 시작하기';
    return () => {
      if (velocityTimer.current) clearTimeout(velocityTimer.current);
    };
  }, []);

  // 동의 단계 완료
  const handleConsentComplete = () => {
    if (!agreed) return;
    onboard();
    setStep('intro');
  };

  // 캘리브레이션 시작 (Easy 단계 진입)
  const startCalibrationEasy = () => {
    setScrollVelocities([]);
    setCurrentVelocity(0);
    lastScrollY.current = 0;
    lastScrollTime.current = Date.now();
    setStep('calibration_easy');
  };

  // Calibration Easy 완료
  const completeCalibrationEasy = () => {
    const avg = scrollVelocities.length > 0 
      ? parseFloat((scrollVelocities.reduce((a, b) => a + b, 0) / scrollVelocities.length).toFixed(3))
      : 0.4; // 디폴트 값
    setEasyBaseline(avg);
    
    // Hard 단계 준비
    setScrollVelocities([]);
    setCurrentVelocity(0);
    lastScrollY.current = 0;
    lastScrollTime.current = Date.now();
    setStep('calibration_hard');
  };

  // Calibration Hard 완료
  const completeCalibrationHard = () => {
    const avg = scrollVelocities.length > 0 
      ? parseFloat((scrollVelocities.reduce((a, b) => a + b, 0) / scrollVelocities.length).toFixed(3))
      : 0.25; // 디폴트 값
    setHardBaseline(avg);
    
    // 로컬 스토리지 및 Zustand 저장
    const easyVal = easyBaseline || 0.4;
    setBaseline(easyVal, avg);
    setStep('result');
  };

  // 스크롤 이벤트 감지 및 스크롤 속도 누적 계산
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const scrollTop = el.scrollTop;
    const now = Date.now();
    
    const deltaY = Math.abs(scrollTop - lastScrollY.current);
    const deltaT = now - lastScrollTime.current; // ms
    
    if (deltaY > 2 && deltaT > 20) {
      const velocity = parseFloat((deltaY / deltaT).toFixed(3)); // px/ms
      if (velocity > 0.01 && velocity < 10) {
        setCurrentVelocity(velocity);
        setScrollVelocities(prev => [...prev, velocity]);

        // 스크롤 멈추면 실시간 속도 표시를 0으로 서서히 초기화
        if (velocityTimer.current) clearTimeout(velocityTimer.current);
        velocityTimer.current = setTimeout(() => {
          setCurrentVelocity(0);
        }, 300);
      }
    }
    
    lastScrollY.current = scrollTop;
    lastScrollTime.current = now;
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-10"
      style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
    >
      <div
        className="w-full max-w-lg rounded-2xl border p-8 transition-all duration-300"
        style={{
          backgroundColor: 'var(--color-surface)',
          borderColor: 'var(--color-border)',
          boxShadow: 'var(--shadow-md, 0 8px 30px rgba(0,0,0,0.08))',
        }}
      >
        {/* 1. 개인정보 동의 단계 */}
        {step === 'consent' && (
          <div>
            <div className="text-center mb-6">
              <div className="flex justify-center mb-4 select-none" style={{ color: 'var(--color-primary)' }}><Brain size={48} strokeWidth={1.5} /></div>
              <h1
                className="text-xl font-bold"
                style={{ color: 'var(--color-primary)', letterSpacing: 'var(--tracking-kr)' }}
              >
                AI 리터러시 케어
              </h1>
              <p className="mt-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                GPT는 글을 대신 읽어주지만,<br />우리는 당신의 <b style={{ color: 'var(--color-text)' }}>문해력 성장</b>을 관리합니다.
              </p>
            </div>

            <div
              className="rounded-lg p-4 mb-4 text-sm"
              style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}
            >
              <div className="flex items-center gap-2 font-semibold mb-2">
                <span style={{ color: 'var(--color-text-secondary)' }}><User size={16} /></span>
                <span>익명으로 시작</span>
              </div>
              <p style={{ color: 'var(--color-text-secondary)', lineHeight: 'var(--leading-normal)' }}>
                이메일·비밀번호 없이 <b style={{ color: 'var(--color-text)' }}>익명 ID</b>가 자동 발급됩니다.
                읽기 기록은 이 브라우저에만 연결되며 언제든 초기화할 수 있습니다.
              </p>
            </div>

            <div
              className="rounded-lg p-4 mb-5 text-xs"
              style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}
            >
              <div className="font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
                <ClipboardList size={16} style={{ color: 'var(--color-text-secondary)' }} />
                개인정보 처리 안내
              </div>
              <ul className="space-y-1 list-disc pl-4">
                <li>수집 항목: 익명 ID, 읽기 행동(스크롤·체류·이탈), 퀴즈 응답</li>
                <li>수집 목적: 실시간 집중도 분석 및 문해력 성장 리포트 제공</li>
                <li>보관/파기: 브라우저 로컬 및 데모 서버, 세션 초기화 시 삭제</li>
                <li>제3자 제공 없음 · 민감정보 미수집</li>
              </ul>
            </div>

            <label className="flex items-start gap-2 mb-5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                style={{ marginTop: 3, width: 16, height: 16, accentColor: 'var(--color-primary)' }}
              />
              <span className="text-sm" style={{ color: 'var(--color-text)' }}>
                위 개인정보 처리 안내를 확인했으며, 익명 데이터 수집에 동의합니다. <span style={{ color: 'var(--color-danger)' }}>(필수)</span>
              </span>
            </label>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              disabled={!agreed}
              onClick={handleConsentComplete}
              style={{ opacity: agreed ? 1 : 0.5, cursor: agreed ? 'pointer' : 'not-allowed' }}
            >
              동의하고 시작하기 →
            </Button>
          </div>
        )}

        {/* 2. 안내 및 준비 단계 */}
        {step === 'intro' && (
          <div className="text-center">
            <div className="flex justify-center mb-5" style={{ color: 'var(--color-primary)' }}><Timer size={48} strokeWidth={1.5} /></div>
            <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--color-primary)' }}>
              개인 맞춤형 독서 분석 설정
            </h2>
            <p className="text-sm mb-6" style={{ color: 'var(--color-text-secondary)', lineHeight: '1.6' }}>
              사람마다 글을 읽고 이해하는 속도는 다릅니다.<br />
              보다 정밀한 실시간 집중도 측정을 위해,<br />
              <strong>2가지 간단한 글</strong>을 읽는 동안 평소 독서 스타일을 분석합니다.<br />
              <span style={{ color: 'var(--color-primary-light, #3b82f6)' }}>평소 기사를 읽는 속도로 자연스럽게 스크롤하며 읽어주세요!</span>
            </p>

            <div 
              className="rounded-lg p-4 mb-6 text-left text-xs"
              style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}
            >
              <div className="font-semibold mb-2 flex items-center gap-1.5"><Lightbulb size={14} style={{ color: '#fbbf24' }} /> 측정 진행 가이드</div>
              <ol className="list-decimal pl-4 space-y-1" style={{ color: 'var(--color-text-secondary)' }}>
                <li>텍스트 박스 내부를 아래로 천천히 스크롤하며 읽습니다.</li>
                <li>마지막 단락까지 모두 읽으신 후 아래 <b>[다 읽었습니다]</b> 버튼을 누릅니다.</li>
                <li>쉬운 글(일상 글)과 어려운 글(과학/학술 지문) 각 1편씩 측정됩니다.</li>
              </ol>
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={startCalibrationEasy}
            >
              <span className="flex items-center justify-center gap-2">독서 스타일 분석 시작 <Rocket size={18} /></span>
            </Button>
          </div>
        )}

        {/* 3. Calibration Easy 단계 */}
        {step === 'calibration_easy' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <span className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 font-semibold">
                <Book size={14} /> 1단계: 쉬운 글 읽기
              </span>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                실시간 속도: <strong className="text-blue-500">{currentVelocity} px/ms</strong>
              </span>
            </div>

            <h3 className="text-lg font-bold mb-3">인류와 불의 역사</h3>
            
            <div
              onScroll={handleScroll}
              className="overflow-y-auto border rounded-lg p-4 mb-5 select-none animate-fadeIn"
              style={{
                height: '240px',
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-surface-alt)',
                lineHeight: '1.7',
                fontSize: '0.95rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              {EASY_TEXTS.map((txt, idx) => (
                <p key={idx} className="mb-4">{txt}</p>
              ))}
              <div className="text-center text-xs py-4 border-t border-dashed" style={{ color: 'var(--color-text-muted)' }}>
                ✨ 텍스트의 끝입니다. 다 읽으셨다면 아래 버튼을 눌러주세요.
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              disabled={scrollVelocities.length < 15}
              onClick={completeCalibrationEasy}
              style={{ opacity: scrollVelocities.length >= 15 ? 1 : 0.6 }}
            >
              {scrollVelocities.length < 15 ? "더 안정적인 속도 측정을 위해 글을 조금 더 읽어주세요..." : <span className="flex items-center justify-center gap-2">다 읽었습니다 <CheckCircle2 size={18} /></span>}
            </Button>
          </div>
        )}

        {/* 4. Calibration Hard 단계 */}
        {step === 'calibration_hard' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <span className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 font-semibold">
                <BookOpen size={14} /> 2단계: 어려운 글 읽기
              </span>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                실시간 속도: <strong className="text-purple-500">{currentVelocity} px/ms</strong>
              </span>
            </div>

            <h3 className="text-lg font-bold mb-3">양자역학의 결정론 논쟁</h3>
            
            <div
              onScroll={handleScroll}
              className="overflow-y-auto border rounded-lg p-4 mb-5 select-none animate-fadeIn"
              style={{
                height: '240px',
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-surface-alt)',
                lineHeight: '1.7',
                fontSize: '0.95rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              {HARD_TEXTS.map((txt, idx) => (
                <p key={idx} className="mb-4">{txt}</p>
              ))}
              <div className="text-center text-xs py-4 border-t border-dashed" style={{ color: 'var(--color-text-muted)' }}>
                ✨ 텍스트의 끝입니다. 다 읽으셨다면 아래 버튼을 눌러주세요.
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              disabled={scrollVelocities.length < 15}
              onClick={completeCalibrationHard}
              style={{ opacity: scrollVelocities.length >= 15 ? 1 : 0.6 }}
            >
              {scrollVelocities.length < 15 ? "더 안정적인 속도 측정을 위해 글을 조금 더 읽어주세요..." : <span className="flex items-center justify-center gap-2">분석 완료하기 <Flag size={18} /></span>}
            </Button>
          </div>
        )}

        {/* 5. 분석 완료 결과 피드백 단계 */}
        {step === 'result' && (
          <div className="text-center">
            <div className="flex justify-center mb-5" style={{ color: 'var(--color-primary)' }}><BarChart2 size={48} strokeWidth={1.5} /></div>
            <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-primary)' }}>
              독서 스타일 분석 완료!
            </h2>
            <p className="text-sm mb-6" style={{ color: 'var(--color-text-secondary)' }}>
              회원님의 읽기 스크롤 특성을 바탕으로 기준 스펙이 맞춤형으로 설정되었습니다.
            </p>

            <div 
              className="rounded-xl border p-5 mb-6 text-left"
              style={{ 
                backgroundColor: 'var(--color-surface-alt)', 
                borderColor: 'var(--color-border)' 
              }}
            >
              <h4 className="font-semibold text-sm mb-4 flex items-center gap-1.5">
                <ClipboardList size={16} style={{ color: 'var(--color-text-secondary)' }} /> 나의 독서 스크롤 기준선
              </h4>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                    <span>쉬운 글 (일반/설명문)</span>
                    <span className="font-bold text-blue-500">{easyBaseline} px/ms</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-blue-500 h-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, ((easyBaseline || 0.4) / 3.0) * 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                    <span>어려운 글 (학술/논설문)</span>
                    <span className="font-bold text-purple-500">{hardBaseline} px/ms</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-purple-500 h-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, ((hardBaseline || 0.25) / 3.0) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="text-[11px] mt-5 p-3 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 leading-relaxed flex gap-2 items-start">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>이 기준선보다 과도하게 빠른 속도로 스크롤할 경우 <b>"대충 훑어 읽기(Skimming)"</b>로 감지되어 실시간 집중도 케어 비서가 작동합니다.</span>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full animate-bounce"
              onClick={() => navigate('/home', { replace: true })}
            >
              <span className="flex items-center justify-center gap-2">케어 시작하기! <Target size={18} /></span>
            </Button>
          </div>
        )}
      </div>

      {/* 7/11: 회원가입 후 즉시 진입 시 튜토리얼 팝업 오버레이 */}
      {isAuthenticated && user && !user.onboardingCompleted && <TutorialModal />}
    </div>
  );
}
