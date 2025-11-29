import { BrowserRouter, Route, Routes } from "react-router-dom";
import QuestionsPage from "./pages/QuestionsPage.jsx";
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import CourseConfigPage from './pages/CourseConfigPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/course/:courseId/config" element={<CourseConfigPage />} />
        <Route path="/course/:courseId" element={<QuestionsPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
