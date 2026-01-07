import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import QuizExamView from "../components/quiz/QuizExamView";
import QuizReviewView from "../components/quiz/QuizReviewView";
import { fetchCourses, fetchChapters, fetchChapterQuiz, exportChapterQuiz } from "../api";
import { ArrowLeft, BookOpen, Eye, PenTool, ChevronDown, Download, X, FileText, CheckSquare, AlertCircle } from "lucide-react";

const ExportModal = ({ isOpen, onClose, onExport }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 transform transition-all scale-100">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900">导出题库</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={24} />
          </button>
        </div>

        <div className="space-y-4">
          <button
            onClick={() => onExport(false)}
            className="w-full flex items-center p-4 rounded-xl border-2 border-gray-100 hover:border-blue-500 hover:bg-blue-50 transition-all group text-left"
          >
            <div className="bg-blue-100 p-3 rounded-lg text-blue-600 mr-4 group-hover:bg-blue-200 transition-colors">
              <FileText size={24} />
            </div>
            <div>
              <div className="font-semibold text-gray-900">学生版（无答案）</div>
              <div className="text-sm text-gray-500">仅包含题目，适合打印分发给学生练习</div>
            </div>
          </button>

          <button
            onClick={() => onExport(true)}
            className="w-full flex items-center p-4 rounded-xl border-2 border-gray-100 hover:border-green-500 hover:bg-green-50 transition-all group text-left"
          >
            <div className="bg-green-100 p-3 rounded-lg text-green-600 mr-4 group-hover:bg-green-200 transition-colors">
              <CheckSquare size={24} />
            </div>
            <div>
              <div className="font-semibold text-gray-900">教师版（含答案解析）</div>
              <div className="text-sm text-gray-500">包含题目、完整答案及详细解析</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

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

  // 自定义下拉菜单状态
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // 导出模态框状态
  const [showExportModal, setShowExportModal] = useState(false);

  // 点击外部关闭下拉菜单
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

  // 'review' (看题模式) 或 'exam' (答题模式)
  const [viewMode, setViewMode] = useState('review');

  // 1. 加载课程和章节
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

  // 2. 当章节改变时加载测验
  useEffect(() => {
    const loadQuiz = async () => {
      if (!selectedChapterId) return;

      setQuizLoading(true);
      setQuizData(null);
      // 切换章节时重置为看题模式
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

  const handleExport = async (includeAnswers) => {
    if (!selectedChapterId) return;
    try {
      const response = await exportChapterQuiz(selectedChapterId, includeAnswers);

      // 创建 blob 链接以进行下载
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      // 尝试从标头或默认值获取文件名
      const contentDisposition = response.headers['content-disposition'];
      let filename = `chapter_${selectedChapterId}_quiz.docx`;

      if (contentDisposition) {
        // 优先尝试解析 filename*=UTF-8''... (用于非 ASCII 字符，如中文)
        const filenameStarMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
        if (filenameStarMatch && filenameStarMatch.length === 2) {
          filename = decodeURIComponent(filenameStarMatch[1]);
        } else {
          // 降级尝试解析 filename="..."
          const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
          if (filenameMatch && filenameMatch.length === 2) {
            filename = decodeURIComponent(filenameMatch[1]);
          }
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // 清理
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      setShowExportModal(false);
    } catch (err) {
      console.error("Export failed:", err);
      alert("导出失败，请重试");
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">加载中...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleExport}
      />

      <div className="max-w-5xl mx-auto space-y-6">
        {/* 头部 */}
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

              {/* 自定义下拉菜单 */}
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

            <div className="flex gap-2 items-center flex-wrap">
              {/* 新增的错题本入口 - 红色按钮 */}
              <Link
                to={`/course/${courseId}/mistakes`}
                className="flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 transition-all duration-300 whitespace-nowrap"
                title="查看错题本"
              >
                <AlertCircle size={14} /> 错题本
              </Link>

              {/* 带滑动动画的模式切换器 */}
              <div className="relative flex bg-gray-100 p-1 rounded-lg flex-1 isolate">
                {/* 滑动药丸 */}
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

              {/* 导出按钮 */}
              {quizData && (
                <button
                  onClick={() => setShowExportModal(true)}
                  className="flex items-center justify-center gap-2 px-4 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-50 hover:border-gray-300 transition-all duration-300 shadow-sm whitespace-nowrap"
                  title="导出为 Word"
                >
                  <Download size={14} /> 导出
                </button>
              )}

              {/* 生成按钮 */}
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

        {/* 内容 */}
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