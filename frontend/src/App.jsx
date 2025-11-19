import { BrowserRouter, Route, Routes } from "react-router-dom";
import QuestionsPage from "./pages/QuestionsPage.jsx";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<QuestionsPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;

