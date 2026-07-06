import { RouterProvider } from 'react-router-dom';
import { router } from './app/router';

/**
 * App — 라우터 진입점
 * 6/21: react-router-dom RouterProvider로 전환
 * 실제 레이아웃/페이지는 app/layouts/RootLayout, pages/ 에서 관리
 */
function App() {
  return <RouterProvider router={router} />;
}

export default App;
