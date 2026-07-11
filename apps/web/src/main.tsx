import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/globals.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

// 7/11: 모든 CSS 리셋과 Tailwind 우선순위를 깨부수고 웜 선형 그라데이션 배경 강제 주입
try {
  document.documentElement.style.setProperty('background', 'linear-gradient(180deg, #FAF8F5 0%, #EFEBE0 100%) fixed', 'important');
  document.body.style.setProperty('background', 'linear-gradient(180deg, #FAF8F5 0%, #EFEBE0 100%) fixed', 'important');
} catch (e) {
  console.error(e);
}

