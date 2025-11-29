import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchCourses, fetchChapters, generateCourseCustom } from "../api";
import { ArrowLeft, BookOpen, Sparkles } from "lucide-react";
import GenerationProgress from "../components/GenerationProgress";

const CourseConfigPage = () => {
    const { courseId } = useParams();
    const navigate = useNavigate();

    const [course, setCourse] = useState(null);
    const [chapters, setChapters] = useState([]);
    const [selectedChapterIds, setSelectedChapterIds] = useState([]);
    const [numMc, setNumMc] = useState(5);
    const [numFb, setNumFb] = useState(5);

    const [loading, setLoading] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);

    useEffect(() => {
        const loadData = async () => {
            if (!courseId) return;
            try {
                const courses = await fetchCourses();
                const currentCourse = courses.find(c => c.id === parseInt(courseId));
                setCourse(currentCourse);

                const chs = await fetchChapters(parseInt(courseId));
                setChapters(chs);
                // Default select all
                setSelectedChapterIds(chs.map(c => c.id));
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [courseId]);

    const toggleChapter = (id) => {
        if (selectedChapterIds.includes(id)) {
            setSelectedChapterIds(selectedChapterIds.filter(cid => cid !== id));
        } else {
            setSelectedChapterIds([...selectedChapterIds, id]);
        }
    };

    const handleGenerate = async () => {
        if (selectedChapterIds.length === 0) return;

        setIsGenerating(true);
        try {
            await generateCourseCustom(parseInt(courseId), {
                chapter_ids: selectedChapterIds,
                num_mc: numMc,
                num_fb: numFb
            });
            // GenerationProgress component will handle the rest
        } catch (err) {
            console.error(err);
            alert("启动生成任务失败");
            setIsGenerating(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">加载中...</div>;

    return (
        <main className="min-h-screen bg-gray-50 py-8 px-4">
            {isGenerating && (
                <GenerationProgress
                    courseId={courseId}
                    onComplete={() => navigate(`/course/${courseId}`)}
                />
            )}

            <div className="max-w-3xl mx-auto space-y-6">
                {/* Header */}
                <header className="bg-white rounded-2xl shadow-sm p-6">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center text-gray-500 hover:text-gray-900 mb-4 transition-colors"
                    >
                        <ArrowLeft size={16} className="mr-1" /> 返回首页
                    </button>
                    <h1 className="text-2xl font-bold text-gray-900">配置生成选项</h1>
                    <p className="text-gray-500 mt-1">选择需要生成题目的章节及数量</p>
                </header>

                {/* Course Info */}
                <div className="bg-white rounded-2xl shadow-sm p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-2">{course?.title}</h2>
                    <p className="text-sm text-gray-500">{course?.description}</p>
                </div>

                {/* Configuration */}
                <div className="bg-white rounded-2xl shadow-sm p-6">
                    <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
                        <Sparkles size={20} className="text-blue-600" />
                        题目数量配置 (每章)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                选择题数量
                            </label>
                            <input
                                type="number"
                                min="1"
                                max="20"
                                value={numMc}
                                onChange={(e) => setNumMc(parseInt(e.target.value) || 0)}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                填空题数量
                            </label>
                            <input
                                type="number"
                                min="1"
                                max="20"
                                value={numFb}
                                onChange={(e) => setNumFb(parseInt(e.target.value) || 0)}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Chapter Selection */}
                <div className="bg-white rounded-2xl shadow-sm p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                            <BookOpen size={20} className="text-blue-600" />
                            选择章节
                        </h3>
                        <div className="space-x-2">
                            <button
                                onClick={() => setSelectedChapterIds(chapters.map(c => c.id))}
                                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                            >
                                全选
                            </button>
                            <span className="text-gray-300">|</span>
                            <button
                                onClick={() => setSelectedChapterIds([])}
                                className="text-sm text-gray-500 hover:text-gray-700"
                            >
                                清空
                            </button>
                        </div>
                    </div>

                    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                        {chapters.map((chapter) => (
                            <label
                                key={chapter.id}
                                className={`flex items-center p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedChapterIds.includes(chapter.id)
                                    ? "border-blue-500 bg-blue-50"
                                    : "border-gray-100 hover:border-gray-200"
                                    }`}
                            >
                                <input
                                    type="checkbox"
                                    className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 border-gray-300 mr-3"
                                    checked={selectedChapterIds.includes(chapter.id)}
                                    onChange={() => toggleChapter(chapter.id)}
                                />
                                <span className={`flex-1 font-medium ${selectedChapterIds.includes(chapter.id) ? "text-blue-900" : "text-gray-700"
                                    }`}>
                                    {chapter.title}
                                </span>
                            </label>
                        ))}
                    </div>

                    <div className="mt-4 text-sm text-gray-500 text-right">
                        已选 {selectedChapterIds.length} / {chapters.length} 章
                    </div>
                </div>

                {/* Action Button */}
                <button
                    onClick={handleGenerate}
                    disabled={selectedChapterIds.length === 0 || isGenerating}
                    className={`w-full py-4 rounded-xl font-bold text-lg shadow-lg transition-all transform hover:-translate-y-1 ${selectedChapterIds.length === 0 || isGenerating
                        ? "bg-gray-200 text-gray-400 cursor-not-allowed shadow-none"
                        : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-blue-200 hover:shadow-blue-300"
                        }`}
                >
                    <div className="flex items-center justify-center gap-2">
                        {isGenerating ? (
                            <>
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                正在提交...
                            </>
                        ) : (
                            <>
                                <Sparkles size={24} />
                                开始生成题目
                            </>
                        )}
                    </div>
                </button>
            </div>
        </main>
    );
};

export default CourseConfigPage;
