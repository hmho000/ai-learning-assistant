import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import QuizExamView from "../components/quiz/QuizExamView";
import { fetchCourses, fetchChapters, fetchChapterQuiz } from "../api";
import { ArrowLeft } from "lucide-react";

const QuestionsPage = () => {
  const { id } = useParams(); // courseId
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [selectedChapterId, setSelectedChapterId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [quizData, setQuizData] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);

  // 1. Load Course & Chapters
  useEffect(() => {
    const loadData = async () => {
      if (!id) return;
      setLoading(true);
      try {
        // Fetch all courses to find the current one (API optimization needed later)
        const courses = await fetchCourses();
        const currentCourse = courses.find(c => c.id === parseInt(id));

        if (!currentCourse) {
          throw new Error("Course not found");
        }
        setCourse(currentCourse);

        const chs = await fetchChapters(parseInt(id));
        setChapters(chs);

        if (chs.length > 0) {
          setSelectedChapterId(chs[0].id);
        }
      } catch (err) {
        console.error(err);
        setError("无法加载课程数据");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  // 2. Load Quiz when chapter changes
  useEffect(() => {
    const loadQuiz = async () => {
      if (!selectedChapterId) return;

      setQuizLoading(true);
      setQuizData(null);
      try {
        const quizzes = await fetchChapterQuiz(selectedChapterId);
        // Merge all questions from all quizzes in this chapter
        // For now, we just take the first quiz or merge them
        if (quizzes.length > 0) {
          // Flatten questions if multiple quizzes exist for a chapter
          // But usually 1 chapter -> 1 quiz in our current logic
          // Let's just take the first one for simplicity or merge questions
          const allQuestions = quizzes.flatMap(q => q.questions || []);

          setQuizData({
            title: quizzes[0].title,
            questions: allQuestions
          });
        } else {
          setQuizData(null);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setQuizLoading(false);
      }
    };

    loadQuiz();
  }, [selectedChapterId]);

  const handleChapterChange = (e) => {
    setSelectedChapterId(parseInt(e.target.value));
  };

  if (loading) return <div className="p-8 text-center text-gray-500">加载中...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <header className="bg-white rounded-2xl shadow-sm p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-gray-500 hover:text-gray-900 mb-2 transition-colors"
            >
              <ArrowLeft size={16} className="mr-1" /> 返回课程列表
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              {course?.title}
            </h1>
            <p className="text-gray-500 text-sm mt-1">{course?.description}</p>
          </div>

          <div className="w-full md:w-64">
            <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">当前章节</label>
            <select
              value={selectedChapterId || ""}
              onChange={handleChapterChange}
              className="w-full rounded-lg border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {chapters.map(ch => (
                <option key={ch.id} value={ch.id}>
                  {ch.title}
                </option>
              ))}
            </select>
          </div>
        </header>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-sm min-h-[500px] p-6">
          {quizLoading ? (
            <div className="text-center py-20 text-gray-400">正在加载题目...</div>
          ) : quizData && quizData.questions && quizData.questions.length > 0 ? (
            <QuizExamView
              quiz={quizData}
              chapterId={selectedChapterId}
              courseId={course?.id}
            />
          ) : (
            <div className="text-center py-20 text-gray-400">
              <p>本章节暂无题目</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
};

export default QuestionsPage;
