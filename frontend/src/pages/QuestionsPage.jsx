import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import QuizExamView from "../components/quiz/QuizExamView";
import QuizReviewView from "../components/quiz/QuizReviewView";
import { fetchCourses, fetchChapters, fetchChapterQuiz } from "../api";
import { ArrowLeft, BookOpen, Eye, PenTool, ChevronDown } from "lucide-react";

const QuestionsPage = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [selectedChapterId, setSelectedChapterId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [quizData, setQuizData] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);

  // Custom Dropdown State
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // 'review' (看题模式) or 'exam' (答题模式)
  const [viewMode, setViewMode] = useState('review');

  // 1. Load Course & Chapters
  useEffect(() => {
    const loadData = async () => {
      if (!courseId) return;
      setLoading(true);
      try {
        const courses = await fetchCourses();
        const currentCourse = courses.find(c => c.id === parseInt(courseId));

        if (!currentCourse) {
          throw new Error("Course not found");
        }
        setCourse(currentCourse);

        const chs = await fetchChapters(parseInt(courseId));
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
  }, [courseId]);

  // 2. Load Quiz when chapter changes
  useEffect(() => {
    const loadQuiz = async () => {
      if (!selectedChapterId) return;

      setQuizLoading(true);
      setQuizData(null);
      // Reset to review mode when changing chapters
      setViewMode('review');

      try {
        const quizzes = await fetchChapterQuiz(selectedChapterId);
        if (quizzes.length > 0) {
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

          <div className="flex flex-col gap-3 w-full md:w-auto">
            <div className="w-full md:w-64 relative" ref={dropdownRef}>
              <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">当前章节</label>

              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="w-full flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-left focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 ease-in-out hover:border-blue-300 hover:shadow-sm"
              >
                <span className="truncate block mr-2">
                  {chapters.find(ch => ch.id === selectedChapterId)?.title || "选择章节"}
                  {chapters.find(ch => ch.id === selectedChapterId)?.has_quiz ? " (已生成)" : ""}
                </span>
                <ChevronDown
                  size={16}
                  className={`text-gray-400 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {/* Custom Dropdown Menu */}
              <div
                className={`absolute top-full left-0 w-full mt-1 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-50 transition-all duration-200 origin-top ${isDropdownOpen
                  ? 'opacity-100 scale-100 translate-y-0 visible'
                  : 'opacity-0 scale-95 -translate-y-2 invisible'
                  }`}
              >
                <div className="max-h-64 overflow-y-auto py-1 custom-scrollbar">
                  {chapters.map(ch => (
                    <button
                      key={ch.id}
                      onClick={() => {
                        handleChapterChange({ target: { value: ch.id } });
                        setIsDropdownOpen(false);
                      }}
                      className={`w-full text-left px-4 py-2.5 text-sm transition-colors duration-150 flex items-center justify-between group ${selectedChapterId === ch.id
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-50'
                        }`}
                    >
                      <span className="truncate">{ch.title}</span>
                      {ch.has_quiz && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${selectedChapterId === ch.id
                          ? 'bg-blue-100 text-blue-600'
                          : 'bg-gray-100 text-gray-500 group-hover:bg-gray-200'
                          }`}>
                          已生成
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              {/* Mode Switcher with Sliding Animation */}
              <div className="relative flex bg-gray-100 p-1 rounded-lg flex-1 isolate">
                {/* Sliding Pill */}
                <div
                  className={`absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-md bg-white shadow-sm transition-all duration-300 ease-in-out z-[-1] ${viewMode === 'review' ? 'left-1' : 'left-[calc(50%)]'
                    }`}
                />

                <button
                  onClick={() => setViewMode('review')}
                  className={`flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-300 whitespace-nowrap z-10 ${viewMode === 'review' ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  <Eye size={14} /> 看题
                </button>
                <button
                  onClick={() => setViewMode('exam')}
                  className={`flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-300 whitespace-nowrap z-10 ${viewMode === 'exam' ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  <PenTool size={14} /> 答题
                </button>
              </div>

              {/* Generate Button */}
              <button
                onClick={() => navigate(`/course/${courseId}/config`)}
                className="flex items-center justify-center gap-2 px-4 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-all duration-300 shadow-sm hover:shadow-md whitespace-nowrap"
                title="生成更多题目"
              >
                <BookOpen size={14} /> 生成题目
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-sm min-h-[500px] p-6">
          {quizLoading ? (
            <div className="text-center py-20 text-gray-400">正在加载题目...</div>
          ) : quizData && quizData.questions && quizData.questions.length > 0 ? (
            viewMode === 'review' ? (
              <QuizReviewView
                quiz={quizData}
                onStartExam={() => setViewMode('exam')}
              />
            ) : (
              <QuizExamView
                quiz={quizData}
                chapterId={selectedChapterId}
                courseId={course?.id}
              />
            )
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
