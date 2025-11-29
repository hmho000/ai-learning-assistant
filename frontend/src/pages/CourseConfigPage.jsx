import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchChapters, generateCourseCustom } from '../api';
import { Loader2, CheckCircle, Settings, ArrowRight } from 'lucide-react';

export default function CourseConfigPage() {
    const { courseId } = useParams();
    const navigate = useNavigate();
    const [chapters, setChapters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedChapters, setSelectedChapters] = useState([]);
    const [config, setConfig] = useState({
        num_mc: 5,
        num_fb: 5
    });
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        loadChapters();
    }, [courseId]);

    const loadChapters = async () => {
        try {
            const data = await fetchChapters(Number(courseId));
            setChapters(data);
            // Default select all
            setSelectedChapters(data.map(c => c.id));
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleChapter = (id) => {
        setSelectedChapters(prev =>
            prev.includes(id) ? prev.filter(cid => cid !== id) : [...prev, id]
        );
    };

    const handleStartGeneration = async () => {
        if (selectedChapters.length === 0) return;

        setSubmitting(true);
        try {
            await generateCourseCustom(Number(courseId), {
                chapter_ids: selectedChapters,
                num_mc: config.num_mc,
                num_fb: config.num_fb
            });
            // Redirect to dashboard or course page, maybe with a success param
            navigate('/');
        } catch (err) {
            console.error(err);
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <Loader2 className="animate-spin text-blue-600" size={48} />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-xl p-8">
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                        <Settings size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">生成配置</h1>
                        <p className="text-gray-500">选择需要生成的章节并设置题目数量</p>
                    </div>
                </div>

                <div className="space-y-8">
                    {/* Question Counts */}
                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">每章选择题数量</label>
                            <input
                                type="number"
                                min="1"
                                max="20"
                                value={config.num_mc}
                                onChange={(e) => setConfig({ ...config, num_mc: parseInt(e.target.value) || 0 })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">每章填空题数量</label>
                            <input
                                type="number"
                                min="1"
                                max="20"
                                value={config.num_fb}
                                onChange={(e) => setConfig({ ...config, num_fb: parseInt(e.target.value) || 0 })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>

                    {/* Chapter Selection */}
                    <div>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-gray-900">选择章节 ({selectedChapters.length}/{chapters.length})</h3>
                            <button
                                onClick={() => setSelectedChapters(selectedChapters.length === chapters.length ? [] : chapters.map(c => c.id))}
                                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                            >
                                {selectedChapters.length === chapters.length ? '取消全选' : '全选'}
                            </button>
                        </div>
                        <div className="border border-gray-200 rounded-xl overflow-hidden max-h-96 overflow-y-auto">
                            {chapters.map((chapter) => (
                                <div
                                    key={chapter.id}
                                    onClick={() => handleToggleChapter(chapter.id)}
                                    className={`flex items-center p-4 border-b border-gray-100 last:border-0 cursor-pointer transition-colors ${selectedChapters.includes(chapter.id) ? 'bg-blue-50' : 'hover:bg-gray-50'
                                        }`}
                                >
                                    <div className={`w-5 h-5 rounded border flex items-center justify-center mr-4 ${selectedChapters.includes(chapter.id) ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-300'
                                        }`}>
                                        {selectedChapters.includes(chapter.id) && <CheckCircle size={14} />}
                                    </div>
                                    <span className="text-gray-700 font-medium">{chapter.title}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4 pt-4">
                        <button
                            onClick={() => navigate('/')}
                            className="flex-1 py-3 px-6 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
                        >
                            稍后再说
                        </button>
                        <button
                            onClick={handleStartGeneration}
                            disabled={submitting || selectedChapters.length === 0}
                            className="flex-1 py-3 px-6 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {submitting ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    提交中...
                                </>
                            ) : (
                                <>
                                    开始生成 <ArrowRight size={20} />
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
