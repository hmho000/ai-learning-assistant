import { useEffect, useState } from "react";
import QuestionViewer from "../components/QuestionViewer.jsx";
import QuizExamView from "../components/quiz/QuizExamView";
import { loadQuizJsonByChapter } from "../utils/quizUtils";

const normalizeChapters = (chapters = []) =>
  chapters.map((ch, idx) => {
    const fallbackSource =
      ch.sourceTitle ||
      ch.label ||
      ch.title ||
      (chapters.length === 1 ? "全文" : `章节 ${ch.id ?? idx + 1}`);
    const fallbackQuiz = ch.quizTitle || ch.title || ch.label || fallbackSource;
    return {
      id: ch.id ?? idx + 1,
      sourceTitle: fallbackSource,
      quizTitle: fallbackQuiz,
      file: ch.file,
      description: ch.description || "",
    };
  });

const normalizeCourses = (data) => {
  if (Array.isArray(data.courses) && data.courses.length > 0) {
    return data.courses.map((course, idx) => ({
      id: course.id || `course-${idx + 1}`,
      name: course.name || course.sourceFile || `课程 ${idx + 1}`,
      sourceFile: course.sourceFile || course.name || "",
      chapters: normalizeChapters(course.chapters || []),
    }));
  }

  if (data.course || data.chapters) {
    return [
      {
        id: "default-course",
        name: data.course || "未命名课程",
        sourceFile: data.sourceFile || data.course || "",
        chapters: normalizeChapters(data.chapters || []),
      },
    ];
  }

  return [];
};

const QuestionsPage = () => {
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [selectedChapterId, setSelectedChapterId] = useState(null);
  const [markdownText, setMarkdownText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [manifestLoading, setManifestLoading] = useState(true);
  const [viewMode, setViewMode] = useState("read"); // "read" | "quiz"
  const [quizData, setQuizData] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizError, setQuizError] = useState("");

  const selectedCourse = courses.find((course) => course.id === selectedCourseId);
  const selectedChapter =
    selectedCourse?.chapters.find((ch) => ch.id === selectedChapterId) || null;

  useEffect(() => {
    const loadManifest = async () => {
      try {
        const response = await fetch("/questions/manifest.json");
        if (!response.ok) {
          throw new Error("无法加载课程清单");
        }
        const data = await response.json();
        const normalized = normalizeCourses(data);
        setCourses(normalized);
        if (normalized.length > 0) {
          setSelectedCourseId(normalized[0].id);
          const firstChapter = normalized[0].chapters[0];
          if (firstChapter) {
            setSelectedChapterId(firstChapter.id);
          }
        }
      } catch (err) {
        console.error("加载 manifest 失败：", err);
        setError("无法加载课程清单，请检查 manifest.json 文件。");
      } finally {
        setManifestLoading(false);
      }
    };

    loadManifest();
  }, []);

  const loadMarkdownForChapter = async (chapter) => {
    if (!chapter) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/questions/${chapter.file}`);
      if (!response.ok) {
        throw new Error(`无法加载题库文件：${chapter.file}`);
      }
      const text = await response.text();
      setMarkdownText(text);
    } catch (err) {
      console.error("加载 Markdown 失败：", err);
      setError(err.message || "加载题库失败，请稍后重试。");
      setMarkdownText("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedChapter) {
      loadMarkdownForChapter(selectedChapter);
    }
  }, [selectedChapterId, selectedCourseId]);

  // 章节切换时，重置模式和题库数据
  useEffect(() => {
    setViewMode("read");
    setQuizData(null);
    setQuizError("");
  }, [selectedChapterId]);

  const handleCourseChange = (e) => {
    const newCourseId = e.target.value;
    setSelectedCourseId(newCourseId);
    const nextCourse = courses.find((course) => course.id === newCourseId);
    const firstChapter = nextCourse?.chapters[0];
    setSelectedChapterId(firstChapter ? firstChapter.id : null);
  };

  const handleChapterChange = (e) => {
    const newId = parseInt(e.target.value, 10);
    setSelectedChapterId(newId);
  };

  const displaySourceTitle =
    selectedChapter?.sourceTitle ||
    (selectedCourse?.chapters.length === 1
      ? "全文"
      : selectedCourse?.name || selectedCourse?.sourceFile || "未命名章节");

  const displayQuizTitle =
    selectedChapter?.quizTitle && selectedChapter?.quizTitle !== displaySourceTitle
      ? selectedChapter.quizTitle
      : "";

  const canRenderViewer = !manifestLoading && selectedCourse && selectedChapter;
  const viewerHeading = selectedChapter
    ? `${selectedCourse?.name || selectedCourse?.sourceFile || "未命名课程"} · ${
        selectedChapter.quizTitle || selectedChapter.sourceTitle || "AI 题库"
      }`
    : "";

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white py-10 px-4">
      <div className="max-w-5xl mx-auto space-y-6">
        <header className="bg-white rounded-2xl shadow-subtle px-6 py-6 md:px-10 md:py-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm text-brand-blue font-semibold uppercase tracking-[0.2em]">
                AI Practice Library
              </p>
              <h1 className="text-3xl font-bold text-slate-900 mt-2">
                {displaySourceTitle ? `《${displaySourceTitle}》 ` : ""}
                {displayQuizTitle}
              </h1>
              {selectedChapter?.description ? (
                <p className="text-slate-500 mt-1">{selectedChapter.description}</p>
              ) : (
                <p className="text-slate-500 mt-1">
                  支持多课程、多语言章节标题，自动适配“全文”或英文章节结构。
                </p>
              )}
            </div>
            <div className="flex flex-col w-full md:w-[520px] gap-3">
              <label className="text-sm font-medium text-slate-600">选择课程</label>
              <select
                value={selectedCourseId || ""}
                onChange={handleCourseChange}
                disabled={manifestLoading || courses.length === 0}
                className="rounded-xl border-slate-200 bg-white px-4 py-3 text-slate-800 shadow-inner focus:outline-none focus:ring-2 focus:ring-brand-blue/60 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {courses.length === 0 && <option value="">暂无课程</option>}
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
              <label className="text-sm font-medium text-slate-600">选择章节</label>
              <select
                value={selectedChapterId || ""}
                onChange={handleChapterChange}
                disabled={
                  manifestLoading ||
                  !selectedCourse ||
                  (selectedCourse?.chapters.length || 0) === 0
                }
                className="rounded-xl border-slate-200 bg-white px-4 py-3 text-slate-800 shadow-inner focus:outline-none focus:ring-2 focus:ring-brand-blue/60 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {(!selectedCourse || selectedCourse.chapters.length === 0) && (
                  <option value="">暂无章节</option>
                )}
                {selectedCourse?.chapters.map((chapter) => (
                  <option key={chapter.id} value={chapter.id}>
                    {chapter.sourceTitle || chapter.quizTitle || `章节 ${chapter.id}`}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </header>

        {manifestLoading && (
          <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
            正在加载课程与章节清单…
          </div>
        )}

        {!manifestLoading && !selectedCourse && (
          <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
            当前暂无可用课程，请先运行 Python 脚本生成题库。
          </div>
        )}

        {canRenderViewer && (
          <>
            {loading && (
              <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
                正在加载题库，请稍候…
              </div>
            )}

            {!loading && error && (
              <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-red-500">
                {error}
              </div>
            )}

            {!loading && !error && markdownText === "" && (
              <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
                当前章节暂无题库，请稍后再试。
              </div>
            )}

            {!loading && !error && markdownText !== "" && (
              <>
                <div className="flex gap-2 mb-4">
                  <button
                    className={`px-3 py-1 rounded ${
                      viewMode === "read"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200"
                    }`}
                    onClick={() => setViewMode("read")}
                  >
                    阅读题库
                  </button>

                  <button
                    className={`px-3 py-1 rounded ${
                      viewMode === "quiz"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200"
                    }`}
                    onClick={async () => {
                      setViewMode("quiz");
                      if (!quizData) {
                        try {
                          setQuizLoading(true);
                          setQuizError("");
                          const data = await loadQuizJsonByChapter(
                            selectedChapterId
                          );
                          setQuizData(data);
                        } catch (err) {
                          console.error(err);
                          setQuizError("加载题库失败，请稍后重试。");
                        } finally {
                          setQuizLoading(false);
                        }
                      }
                    }}
                  >
                    开始答题
                  </button>
                </div>

                {viewMode === "read" && (
                  <QuestionViewer
                    markdownText={markdownText}
                    heading={viewerHeading}
                    key={`${selectedCourseId}-${selectedChapterId}`}
                  />
                )}

                {viewMode === "quiz" && (
                  <>
                    {quizLoading && (
                      <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
                        题库加载中...
                      </div>
                    )}
                    {quizError && (
                      <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-red-500">
                        {quizError}
                      </div>
                    )}
                    {quizData && (
                      <QuizExamView
                        quiz={quizData}
                        chapterId={selectedChapterId}
                        courseId={selectedCourseId}
                      />
                    )}
                  </>
                )}
              </>
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default QuestionsPage;
