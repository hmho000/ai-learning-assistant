import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Plus, ArrowRight, Loader2, CheckCircle2, Trash2, AlertCircle } from 'lucide-react';
import { fetchCourses, deleteCourse } from '../api';
import CourseProgressBar from '../components/CourseProgressBar';

export default function DashboardPage() {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const pollInterval = useRef(null);

    const loadCourses = async (isPolling = false) => {
        try {
            if (!isPolling) setLoading(true);
            const data = await fetchCourses();
            setCourses(data);
            setError(null);

            // 检查是否有课程需要轮询
            const hasActiveJobs = data.some(c =>
                ['processing', 'parsing', 'generating'].includes(c.status)
            );

            if (hasActiveJobs) {
                if (!pollInterval.current) {
                    pollInterval.current = setInterval(() => loadCourses(true), 3000);
                }
            } else {
                if (pollInterval.current) {
                    clearInterval(pollInterval.current);
                    pollInterval.current = null;
                }
            }

        } catch (err) {
            console.error(err);
            if (!isPolling) setError("无法加载课程列表");
        } finally {
            if (!isPolling) setLoading(false);
        }
    };

    useEffect(() => {
        loadCourses();
        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current);
        };
    }, []);

    const handleDelete = async (e, courseId) => {
        e.preventDefault(); // 阻止导航
        if (!window.confirm("确定要删除这个课程吗？")) return;

        try {
            await deleteCourse(courseId);
            setCourses(prev => prev.filter(c => c.id !== courseId));
        } catch (err) {
            console.error(err);
            alert("删除失败");
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <Loader2 className="animate-spin text-blue-600" size={32} />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">我的课程</h1>
                        <p className="text-gray-500 mt-2">管理您的学习资料和题库</p>
                    </div>
                    <Link
                        to="/upload"
                        className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200"
                    >
                        <Plus size={20} />
                        <span>新建课程</span>
                    </Link>
                </div>

                {error && (
                    <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-2">
                        <AlertCircle size={20} />
                        {error}
                    </div>
                )}

                {courses.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-2xl shadow-sm border border-gray-100">
                        <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
                            <BookOpen className="text-gray-300" size={40} />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">还没有课程</h3>
                        <p className="text-gray-500 mb-8">上传您的第一本 PDF 教材，开始 AI 辅助学习</p>
                        <Link
                            to="/upload"
                            className="inline-flex items-center gap-2 text-blue-600 font-medium hover:underline"
                        >
                            去上传 <ArrowRight size={16} />
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {courses.map(course => (
                            <Link
                                key={course.id}
                                to={`/course/${course.id}`}
                                className="group bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-all relative block"
                            >
                                {/* 删除按钮 */}
                                <button
                                    onClick={(e) => handleDelete(e, course.id)}
                                    className="absolute top-4 right-4 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors z-10"
                                    title="删除课程"
                                >
                                    <Trash2 size={16} />
                                </button>

                                {/* 状态徽章（仅用于错误或就绪状态，活动任务使用进度条） */}
                                <div className="absolute top-4 left-4">
                                    {course.status === 'error' ? (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-red-50 text-red-700 text-xs font-medium">
                                            <AlertCircle size={12} /> 错误
                                        </span>
                                    ) : course.status === 'ready' && (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-50 text-green-700 text-xs font-medium">
                                            <CheckCircle2 size={12} /> 已就绪
                                        </span>
                                    )}
                                </div>

                                <div className="flex items-start justify-between mb-4 mt-8">
                                    <div className={`p-3 rounded-lg transition-colors ${course.status === 'ready' ? 'bg-blue-50 text-blue-600 group-hover:bg-blue-100' : 'bg-gray-100 text-gray-400'
                                        }`}>
                                        <BookOpen size={24} />
                                    </div>
                                </div>

                                <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-1 pr-8">
                                    {course.title}
                                </h3>
                                <p className="text-sm text-gray-500 line-clamp-2 mb-4 h-10">
                                    {course.description || "暂无描述"}
                                </p>

                                {/* 进度条或操作链接 */}
                                {['processing', 'parsing', 'generating'].includes(course.status) ? (
                                    <CourseProgressBar course={course} />
                                ) : (
                                    <div className={`flex items-center text-sm font-medium ${course.status === 'ready' ? 'text-blue-600' : 'text-gray-400'
                                        }`}>
                                        {course.status === 'ready' ? (
                                            <>进入学习 <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" /></>
                                        ) : course.status === 'error' ? (
                                            <span className="text-red-500">生成失败</span>
                                        ) : (
                                            <>等待处理...</>
                                        )}
                                    </div>
                                )}
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
