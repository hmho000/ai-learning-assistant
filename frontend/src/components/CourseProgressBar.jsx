import React, { useEffect, useState } from 'react';
import { Loader2, Sparkles } from 'lucide-react';

const CourseProgressBar = ({ course }) => {
    const [visualProgress, setVisualProgress] = useState(0);
    const { generation_current_chapter, generation_total_chapters, generation_status_message } = course;

    // Calculate real progress from backend data
    const realProgress = generation_total_chapters > 0
        ? Math.min(100, Math.round((generation_current_chapter / generation_total_chapters) * 100))
        : 0;

    useEffect(() => {
        // Initialize visual progress if it's far behind (e.g. page reload)
        // But don't jump ahead if we are already simulating
        setVisualProgress(prev => {
            if (prev < realProgress) return realProgress;
            return prev;
        });
    }, [realProgress]);

    useEffect(() => {
        // Fake progress logic
        // We want to slowly increment visualProgress even if realProgress doesn't change
        // But we must not exceed realProgress + 15% (and max 99% if not done)

        const interval = setInterval(() => {
            setVisualProgress(prev => {
                // If we are actually done, jump to 100
                if (course.status === 'ready') return 100;

                // Cap fake progress
                const maxFake = Math.min(99, realProgress + 15);

                if (prev >= maxFake) {
                    return prev;
                }

                // Increment by small random amount
                const increment = Math.random() * 0.5;
                return Math.min(maxFake, prev + increment);
            });
        }, 500);

        return () => clearInterval(interval);
    }, [realProgress, course.status]);

    return (
        <div className="mt-4">
            <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-medium text-blue-600 flex items-center gap-1">
                    <Loader2 size={10} className="animate-spin" />
                    {generation_status_message || "正在生成..."}
                </span>
                <span className="text-xs font-bold text-blue-700">
                    {Math.round(visualProgress)}%
                </span>
            </div>
            <div className="w-full bg-blue-100 rounded-full h-2 overflow-hidden">
                <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out relative overflow-hidden"
                    style={{ width: `${visualProgress}%` }}
                >
                    <div className="absolute inset-0 bg-white/30 animate-[shimmer_2s_infinite]"></div>
                </div>
            </div>
            <style>{`
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
            `}</style>
        </div>
    );
};

export default CourseProgressBar;
