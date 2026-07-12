import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Button } from '../components/common/Button';
import { Brain, Activity, Target, CheckCircle2, ArrowRight } from 'lucide-react';
import { motion, type Variants } from 'framer-motion'; // 디자인 강화를 위한 모션 라이브러리 추가

// Stagger 애니메이션 변수 설정
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.1 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 15 } }
};

export default function SignUpPage() {
  const navigate = useNavigate();
  const { signUp, isLoading, error, setError } = useAuthStore();
  
  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 시작하기';
    setError(null);
  }, [setError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !nickname || !password) return;

    try {
      await signUp(email, password, nickname);
      navigate('/onboarding', { replace: true });
    } catch (err) {}
  };

  if (!showForm) {
    return (
      <div className="min-h-screen flex flex-col" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
        {/* 네비게이션 바 */}
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full flex items-center justify-between px-6 py-4 border-b" 
          style={{ borderColor: 'var(--color-border)' }}
        >
          <div className="flex items-center gap-2" style={{ color: 'var(--color-primary)' }}>
            <motion.div
              animate={{ rotate: [0, -10, 10, -10, 10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 5 }}
            >
              <Brain size={28} strokeWidth={2} />
            </motion.div>
            <span className="font-bold text-lg tracking-wide">AllDayHappyDay</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-semibold hidden sm:inline-block" style={{ color: 'var(--color-text-secondary)' }}>
              Contact Sales
            </span>
            <Link to="/login" className="text-sm font-semibold hover:underline" style={{ color: 'var(--color-text)' }}>
              Log in
            </Link>
          </div>
        </motion.header>

        {/* Hero Section */}
        <main className="flex-1 flex flex-col items-center justify-center px-4 pt-16 pb-12 overflow-hidden">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="text-center max-w-3xl mb-12"
          >
            <motion.h1 variants={itemVariants} className="text-4xl md:text-5xl font-extrabold mb-6 leading-tight tracking-tight" style={{ color: 'var(--color-text)' }}>
              당신의 뇌 근육을 키워주는<br className="hidden md:block" /> AI 리터러시 케어
            </motion.h1>
            
            <motion.p variants={itemVariants} className="text-lg md:text-xl mb-8 max-w-2xl mx-auto leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
              글을 대신 읽어주는 것을 넘어, 스스로 읽고 이해할 수 있도록 집중도를 분석하고 퀴즈를 제공합니다.
            </motion.p>
            
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-center justify-center gap-4 relative">
              {/* 버튼 주변 펄스 애니메이션 (AI 느낌) */}
              <motion.div
                className="absolute inset-0 rounded-lg -z-10"
                style={{ backgroundColor: 'var(--color-primary)', opacity: 0.3, filter: 'blur(15px)' }}
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowForm(true)}
                className="flex items-center justify-center gap-2 px-8 py-3.5 rounded-lg text-white font-bold text-lg shadow-lg relative z-10"
                style={{ backgroundColor: 'var(--color-primary)' }}
              >
                가입하기 무료입니다 <ArrowRight size={20} />
              </motion.button>
              
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link
                  to="/login"
                  className="flex items-center justify-center gap-2 px-8 py-3.5 rounded-lg font-bold text-lg border-2"
                  style={{ borderColor: 'var(--color-border)', color: 'var(--color-text)' }}
                >
                  로그인하기
                </Link>
              </motion.div>
            </motion.div>
            
            <motion.p variants={itemVariants} className="text-[11px] mt-6" style={{ color: 'var(--color-text-muted)' }}>
              가입함으로써 이용 약관 및 개인정보처리방침에 동의하는 것으로 간주됩니다.
            </motion.p>
          </motion.div>

          {/* 하단 Feature Showcase Cards */}
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl px-4 pb-16"
          >
            {/* 1번 카드 */}
            <motion.div variants={itemVariants} whileHover={{ y: -8, boxShadow: '0 15px 30px rgba(0,0,0,0.1)' }} className="rounded-xl border overflow-hidden flex flex-col transition-shadow" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
              <div className="h-40 w-full flex flex-col items-center justify-center bg-gradient-to-br from-blue-500/10 to-purple-500/10 p-6 relative">
                <div className="w-full max-w-[200px] h-20 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col justify-center px-4 border border-blue-100 dark:border-blue-900/30">
                   <div className="flex justify-between items-center mb-2">
                     <span className="text-[10px] font-bold text-blue-500 uppercase tracking-wider">스크롤 속도 모니터링</span>
                     <Activity size={14} className="text-blue-500" />
                   </div>
                   <div className="w-full bg-gray-100 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden">
                     <motion.div 
                       initial={{ width: '0%' }}
                       whileInView={{ width: '70%' }}
                       transition={{ duration: 1.5, delay: 0.5, ease: 'easeOut' }}
                       className="bg-blue-500 h-full" 
                     />
                   </div>
                </div>
              </div>
              <div className="p-6 flex-1">
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--color-text)' }}>실시간 집중도 모니터링</h3>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>스크롤 속도와 체류 시간을 분석하여 당신의 읽기 집중도를 실시간으로 측정합니다.</p>
              </div>
            </motion.div>

            {/* 2번 카드 */}
            <motion.div variants={itemVariants} whileHover={{ y: -8, boxShadow: '0 15px 30px rgba(0,0,0,0.1)' }} className="rounded-xl border overflow-hidden flex flex-col transition-shadow" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
              <div className="h-40 w-full flex flex-col items-center justify-center bg-gradient-to-br from-amber-500/10 to-orange-500/10 p-6 relative">
                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  whileInView={{ y: 0, opacity: 1 }}
                  transition={{ type: 'spring', bounce: 0.5, delay: 0.8 }}
                  className="w-full max-w-[200px] bg-white dark:bg-gray-800 rounded-lg shadow-lg flex flex-col px-4 py-3 border border-amber-100 dark:border-amber-900/30 relative top-2"
                >
                   <div className="flex items-center gap-2 mb-2">
                     <div className="w-5 h-5 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center"><Target size={12} className="text-amber-500" /></div>
                     <span className="text-[11px] font-bold text-gray-700 dark:text-gray-300">집중력 저하 감지!</span>
                   </div>
                   <p className="text-[10px] text-amber-600 dark:text-amber-400 font-medium mb-3">방금 읽은 단락의 핵심 내용은?</p>
                   <div className="flex gap-2">
                     <button className="flex-1 py-1 rounded bg-amber-500 text-white text-[10px] font-bold">O</button>
                     <button className="flex-1 py-1 rounded bg-gray-100 dark:bg-gray-700 text-[10px] font-bold">X</button>
                   </div>
                </motion.div>
              </div>
              <div className="p-6 flex-1">
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--color-text)' }}>AI 넛지 & 퀴즈</h3>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>이탈이나 훑어 읽기가 감지되면 O/X 퀴즈로 개입하여 다시 몰입을 유도합니다.</p>
              </div>
            </motion.div>

            {/* 3번 카드 */}
            <motion.div variants={itemVariants} whileHover={{ y: -8, boxShadow: '0 15px 30px rgba(0,0,0,0.1)' }} className="rounded-xl border overflow-hidden flex flex-col transition-shadow" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
              <div className="h-40 w-full flex flex-col items-center justify-center bg-gradient-to-br from-green-500/10 to-emerald-500/10 p-6 relative">
                <div className="w-full max-w-[200px] h-20 bg-white dark:bg-gray-800 rounded-lg shadow flex items-end justify-between px-3 pb-3 pt-6 border border-green-100 dark:border-green-900/30">
                   {[40, 60, 80, 100].map((height, i) => (
                     <motion.div 
                       key={i}
                       initial={{ height: '0%' }}
                       whileInView={{ height: `${height}%` }}
                       transition={{ duration: 0.8, delay: 0.8 + (i * 0.1), type: 'spring' }}
                       className={`w-4 rounded-t ${i === 3 ? 'bg-green-500' : 'bg-green-300 dark:bg-green-800/50'} relative`}
                     >
                       {i === 3 && (
                         <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} transition={{ delay: 1.5, type: 'spring' }}>
                           <CheckCircle2 size={12} className="absolute -top-4 -right-1 text-green-500" />
                         </motion.div>
                       )}
                     </motion.div>
                   ))}
                </div>
              </div>
              <div className="p-6 flex-1">
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--color-text)' }}>리터러시 성장 대시보드</h3>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>점진적으로 향상되는 나의 읽기 능력 추이를 주간/월간 차트로 확인하세요.</p>
              </div>
            </motion.div>
          </motion.div>
        </main>
      </div>
    );
  }

  // 가입 폼 뷰 (기존 모달)
  return (
    <div className="min-h-screen flex flex-col" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
      <header className="w-full flex items-center p-6 cursor-pointer" onClick={() => setShowForm(false)}>
         <ArrowRight size={24} className="rotate-180 mr-2" style={{ color: 'var(--color-text-secondary)' }} />
         <span className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>이전으로</span>
      </header>
      <div className="flex-1 flex items-center justify-center px-4 pb-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: 'spring', damping: 20, stiffness: 100 }}
          className="w-full max-w-md rounded-2xl border p-8"
          style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', boxShadow: 'var(--shadow-md, 0 8px 30px rgba(0,0,0,0.08))' }}
        >
          {/* 타이틀 */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4 select-none" style={{ color: 'var(--color-primary)' }}>
              <Brain size={48} strokeWidth={1.5} />
            </div>
            <h1 className="text-xl font-bold" style={{ color: 'var(--color-primary)', letterSpacing: 'var(--tracking-kr)' }}>
              초기 등록자 회원가입
            </h1>
            <p className="mt-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              AI 리터러시 케어 서비스 이용을 위해 계정을 생성합니다.
            </p>
          </div>

          {error && (
            <div className="rounded-lg p-3.5 mb-5 text-xs text-center border border-red-500/20 font-semibold" style={{ backgroundColor: 'rgba(239, 68, 68, 0.08)', color: '#ef4444' }}>
              ⚠️ {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>이메일 주소</label>
              <input type="email" required placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>닉네임</label>
              <input type="text" required placeholder="홍길동" value={nickname} onChange={(e) => setNickname(e.target.value)} className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>비밀번호</label>
              <input type="password" required placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none" style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }} />
            </div>
            <Button type="submit" variant="primary" size="lg" className="w-full" disabled={isLoading || !email || !nickname || !password} style={{ marginTop: '20px' }}>
              {isLoading ? '등록 중...' : '회원 등록하고 시작하기'}
            </Button>
          </form>
          <div className="mt-6 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
            이미 계정이 있으신가요? <Link to="/login" className="font-semibold text-blue-500 hover:underline">로그인하기</Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
