import { BrowserRouter, Route, Routes } from "react-router-dom";
import QuestionsPage from "./pages/QuestionsPage.jsx";
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import CourseConfigPage from './pages/CourseConfigPage';
import MistakeBookPage from './pages/MistakeBookPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/course/:courseId/config" element={<CourseConfigPage />} />
        <Route path="/course/:courseId/mistakes" element={<MistakeBookPage />} />
        <Route path="/course/:courseId" element={<QuestionsPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
