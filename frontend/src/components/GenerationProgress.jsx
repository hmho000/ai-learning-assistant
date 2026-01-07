import React, { useEffect, useState } from 'react';
import { fetchCourses } from '../api';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, Sparkles } from 'lucide-react';

const GenerationProgress = ({ courseId, onComplete }) => {
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState("正在初始化...");
    const [isComplete, setIsComplete] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        let intervalId;

        const checkProgress = async () => {
            try {
                const courses = await fetchCourses();
                const course = courses.find(c => c.id === parseInt(courseId));

                if (course) {
                    const { generation_total_chapters, generation_current_chapter, generation_status_message, status } = course;

                    setStatusMessage(generation_status_message || "正在处理...");

                    if (generation_total_chapters > 0) {
                        const percentage = Math.min(100, Math.round((generation_current_chapter / generation_total_chapters) * 100));
                        setProgress(percentage);
                    }

                    if (status === 'ready') {
                        setProgress(100);
                        setIsComplete(true);
                        setStatusMessage("生成完成！即将跳转...");
                        clearInterval(intervalId);
                        setTimeout(() => {
                            if (onComplete) {
                                onComplete();
                            } else {
                                navigate(`/course/${courseId}`);
                            }
                        }, 1500);
                    } else if (status === 'error') {
                        setStatusMessage("生成过程中发生错误，请重试。");
                        clearInterval(intervalId);
                    }
                }
            } catch (error) {
                console.error("Failed to poll progress:", error);
            }
        };

        // 初始检查
        checkProgress();
        // 每 1 秒轮询一次
        intervalId = setInterval(checkProgress, 1000);

        return () => clearInterval(intervalId);
    }, [courseId, navigate, onComplete]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/90 backdrop-blur-sm transition-opacity duration-300">
            <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-2xl transform transition-all scale-100">
                <div className="text-center space-y-6">

                    {/* 图标 / 动画 */}
                    <div className="relative flex items-center justify-center w-24 h-24 mx-auto">
                        {isComplete ? (
                            <div className="absolute inset-0 flex items-center justify-center bg-green-100 rounded-full animate-bounce-small">
                                <CheckCircle className="w-12 h-12 text-green-600" />
                            </div>
                        ) : (
                            <>
                                <div className="absolute inset-0 border-4 border-blue-100 rounded-full"></div>
                                <div
                                    className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"
                                    style={{ animationDuration: '1.5s' }}
                                ></div>
                                <Sparkles className="absolute w-8 h-8 text-blue-500 animate-pulse" />
                            </>
                        )}
                    </div>

                    {/* 文本内容 */}
                    <div className="space-y-2">
                        <h2 className="text-2xl font-bold text-gray-900">
                            {isComplete ? "生成完成" : "AI 正在生成课程"}
                        </h2>
                        <p className="text-gray-500 font-medium animate-pulse-slow">
                            {statusMessage}
                        </p>
                    </div>

                    {/* 进度条 */}
                    <div className="relative pt-4">
                        <div className="flex items-center justify-between mb-2 text-sm font-semibold text-gray-600">
                            <span>进度</span>
                            <span>{progress}%</span>
                        </div>
                        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500 ease-out"
                                style={{ width: `${progress}%` }}
                            >
                                <div className="w-full h-full opacity-30 bg-white/30 animate-shimmer"></div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            {/* 自定义动画的 CSS（如果不在全局 CSS 中） */}
            <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
        .animate-bounce-small {
            animation: bounce-small 0.5s infinite alternate;
        }
        @keyframes bounce-small {
            from { transform: translateY(0); }
            to { transform: translateY(-5px); }
        }
      `}</style>
        </div>
    );
};

export default GenerationProgress;
