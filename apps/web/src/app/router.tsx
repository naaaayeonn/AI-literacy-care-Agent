import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import { isOnboarded } from '../stores/sessionConfigStore';
import { useAuthStore } from '../stores/authStore';

// Lazy loading applied for Code Splitting (Performance Optimization)
const ReadingPage = React.lazy(() => import('../pages/ReadingPage'));
const DashboardPage = React.lazy(() => import('../pages/DashboardPage'));
const OnboardingPage = React.lazy(() => import('../pages/OnboardingPage'));
const LandingPage = React.lazy(() => import('../pages/LandingPage'));
const UploadPage = React.lazy(() => import('../pages/UploadPage'));
const ProfilePage = React.lazy(() => import('../pages/ProfilePage'));
const ExtensionPage = React.lazy(() => import('../pages/ExtensionPage'));
const LoginPage = React.lazy(() => import('../pages/LoginPage'));
const SignUpPage = React.lazy(() => import('../pages/SignUpPage'));

// Fallback skeleton loader while fetching chunks (with anti-flicker delay)
const PageLoader = () => {
  const [show, React_setShow] = React.useState(false);

  React.useEffect(() => {
    // 150ms 이내에 로딩이 끝나면 스피너를 아예 보여주지 않음 (깜빡임 방지)
    const timer = setTimeout(() => React_setShow(true), 150);
    return () => clearTimeout(timer);
  }, []);

  if (!show) return <div className="min-h-screen w-full" style={{ backgroundColor: 'var(--color-background)' }} />;

  return (
    <div className="flex min-h-screen items-center justify-center w-full" style={{ backgroundColor: 'var(--color-background)' }}>
      <div 
        className="h-10 w-10 animate-spin rounded-full border-4 border-t-purple-500" 
        style={{ borderColor: 'var(--color-border)', borderTopColor: 'var(--color-primary)' }}
      ></div>
    </div>
  );
};

// 7/11: 초기 구동 시 로컬스토리지 세션 복원
useAuthStore.getState().checkSession();

function IndexRedirect() {
  return <Navigate to={isOnboarded() ? '/home' : '/onboarding'} replace />;
}

// 비로그인 유저 리다이렉트 가드
function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

export const router = createBrowserRouter([
  { path: '/', element: <IndexRedirect /> },
  { path: '/onboarding', element: <Suspense fallback={<PageLoader />}><OnboardingPage /></Suspense> },
  { path: '/login', element: <Suspense fallback={<PageLoader />}><LoginPage /></Suspense> },
  { path: '/signup', element: <Suspense fallback={<PageLoader />}><SignUpPage /></Suspense> },
  { path: '/home', element: <Suspense fallback={<PageLoader />}><LandingPage /></Suspense> },
  { path: '/upload', element: <Suspense fallback={<PageLoader />}><UploadPage /></Suspense> },
  { path: '/extension', element: <Suspense fallback={<PageLoader />}><ExtensionPage /></Suspense> },
  {
    element: <RootLayout />,
    children: [
      { path: '/reading', element: <Suspense fallback={<PageLoader />}><ReadingPage /></Suspense> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/dashboard', element: <Suspense fallback={<PageLoader />}><DashboardPage /></Suspense> },
        ],
      },
      { path: '/profile', element: <Suspense fallback={<PageLoader />}><ProfilePage /></Suspense> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);
