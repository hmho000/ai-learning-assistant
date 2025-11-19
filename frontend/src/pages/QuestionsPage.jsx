import { useEffect, useState } from "react";
import QuestionViewer from "../components/QuestionViewer.jsx";

const QuestionsPage = () => {
  const [chapters, setChapters] = useState([]);
  const [course, setCourse] = useState("数据结构");
  const [selectedChapterId, setSelectedChapterId] = useState(null);
  const [markdownText, setMarkdownText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [manifestLoading, setManifestLoading] = useState(true);

  const selectedChapter = chapters.find((ch) => ch.id === selectedChapterId);

  useEffect(() => {
    const loadManifest = async () => {
      try {
        const response = await fetch("/questions/manifest.json");
        if (!response.ok) {
          throw new Error("无法加载章节清单");
        }
        const data = await response.json();
        setCourse(data.course || "数据结构");
        const sortedChapters = (data.chapters || []).sort((a, b) => a.id - b.id);
        setChapters(sortedChapters);

        if (sortedChapters.length > 0) {
          setSelectedChapterId(sortedChapters[0].id);
        }
      } catch (err) {
        console.error("加载 manifest 失败：", err);
        setError("无法加载章节清单，请检查 manifest.json 文件。");
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
    if (selectedChapterId !== null && selectedChapter) {
      loadMarkdownForChapter(selectedChapter);
    }
  }, [selectedChapterId]);

  const handleChapterChange = (e) => {
    const newId = parseInt(e.target.value, 10);
    setSelectedChapterId(newId);
  };

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
                《{course}》{selectedChapter?.label || "AI生成题库"}
              </h1>
              {selectedChapter?.description && (
                <p className="text-slate-500 mt-1">{selectedChapter.description}</p>
              )}
              {!selectedChapter?.description && (
                <p className="text-slate-500 mt-1">
                  支持多章节切换，方便老师与同学预览、校对与练习。
                </p>
              )}
            </div>
            <div className="flex flex-col w-full md:w-64">
              <label
                htmlFor="chapter-select"
                className="text-sm font-medium text-slate-600 mb-2"
              >
                选择章节
              </label>
              <select
                id="chapter-select"
                value={selectedChapterId || ""}
                onChange={handleChapterChange}
                disabled={manifestLoading || chapters.length === 0}
                className="rounded-xl border-slate-200 bg-white px-4 py-3 text-slate-800 shadow-inner focus:outline-none focus:ring-2 focus:ring-brand-blue/60 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {chapters.length === 0 && (
                  <option value="">暂无章节</option>
                )}
                {chapters.map((chapter) => (
                  <option key={chapter.id} value={chapter.id}>
                    {chapter.shortLabel || chapter.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </header>

        {manifestLoading && (
          <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
            正在加载章节清单…
          </div>
        )}

        {!manifestLoading && chapters.length === 0 && (
          <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-subtle p-8 text-center text-slate-500">
            当前暂无可用章节，请先运行 Python 脚本生成题库。
          </div>
        )}

        {!manifestLoading && chapters.length > 0 && (
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
              <QuestionViewer markdownText={markdownText} key={selectedChapterId} />
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default QuestionsPage;
