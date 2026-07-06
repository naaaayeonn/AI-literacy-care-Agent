import { createBrowserRouter, Navigate } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import ReadingPage from '../pages/ReadingPage';
import DashboardPage from '../pages/DashboardPage';

/**
 * 앱 라우터 정의
 * /           → /reading 으로 리다이렉트
 * /reading    → 읽기 화면 (데모 메인)
 * /dashboard  → 성장 대시보드
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/reading" replace />,
      },
      {
        path: 'reading',
        element: <ReadingPage />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
    ],
  },
]);
