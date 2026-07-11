import { createBrowserRouter, Navigate } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import ReadingPage from '../pages/ReadingPage';
import DashboardPage from '../pages/DashboardPage';
import OnboardingPage from '../pages/OnboardingPage';
import LandingPage from '../pages/LandingPage';
import UploadPage from '../pages/UploadPage';
import ProfilePage from '../pages/ProfilePage';
import ExtensionPage from '../pages/ExtensionPage';
import { isOnboarded } from '../stores/sessionConfigStore';
import LoginPage from '../pages/LoginPage';
import SignUpPage from '../pages/SignUpPage';
import { useAuthStore } from '../stores/authStore';
import { Outlet } from 'react-router-dom';

/**
 * 앱 라우터 정의 (배포 흐름)
 * /            → 온보딩 여부에 따라 /onboarding 또는 /home 으로 분기
 * /onboarding  → 익명 로그인 + 개인정보 동의 (풀스크린)
 * /home        → 모드 선택 랜딩 (실시간 케어 / 업로드 / 확장) (풀스크린)
 * /upload      → 페이지 업로드 (풀스크린)
 * /reading     → 읽기 화면 (헤더 레이아웃)
 * /dashboard   → 성장 대시보드 (헤더 레이아웃)
 * /profile     → 익명 프로필 + 대시보드 (헤더 레이아웃)
 */
// 7/11: 초기 구동 시 로컬스토리지 세션 복원
useAuthStore.getState().checkSession();

function IndexRedirect() {
  return <Navigate to={isOnboarded() ? '/home' : '/onboarding'} replace />;
}

// 7/11: 비로그인 유저 리다이렉트 가드
function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

export const router = createBrowserRouter([
  { path: '/', element: <IndexRedirect /> },
  { path: '/onboarding', element: <OnboardingPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignUpPage /> },
  { path: '/home', element: <LandingPage /> },
  { path: '/upload', element: <UploadPage /> },
  { path: '/extension', element: <ExtensionPage /> },
  {
    element: <RootLayout />,
    children: [
      { path: '/reading', element: <ReadingPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
        ],
      },
      { path: '/profile', element: <ProfilePage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);
