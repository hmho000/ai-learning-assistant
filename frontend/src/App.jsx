import { BrowserRouter, Route, Routes, Navigate, Outlet } from "react-router-dom";
import QuestionsPage from "./pages/QuestionsPage.jsx";
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import CourseConfigPage from './pages/CourseConfigPage';
import MistakeBookPage from './pages/MistakeBookPage';
import LoginPage from './pages/LoginPage';
import MainLayout from './components/MainLayout';

const PrivateRoute = () => {
  const token = localStorage.getItem('token');
  return token ? (
    <MainLayout>
      <Outlet />
    </MainLayout>
  ) : (
    <Navigate to="/login" replace />
  );
};


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<PrivateRoute />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/course/:courseId/config" element={<CourseConfigPage />} />
          <Route path="/course/:courseId/mistakes" element={<MistakeBookPage />} />
          <Route path="/course/:courseId" element={<QuestionsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
