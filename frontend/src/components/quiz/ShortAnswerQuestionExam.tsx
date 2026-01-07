import { useState } from "react";
import { gradeShortAnswer } from "../../api";
import { Sparkles } from "lucide-react";

interface ShortAnswerQuestionExamProps {
    index: number;
    question: {
        id: number;
        question: string;
        answer: string; // Reference answer
        explanation?: string;
    };
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
    showAnswer?: boolean;
}

const ShortAnswerQuestionExam = ({
    index,
    question,
    value,
    onChange,
    disabled = false,
    showAnswer = false,
}: ShortAnswerQuestionExamProps) => {
    const [gradeResult, setGradeResult] = useState<{ score: number; feedback: string } | null>(null);
    const [isGrading, setIsGrading] = useState(false);

    const handleGrade = async () => {
        if (!value.trim()) return;
        setIsGrading(true);
        try {
            const result = await gradeShortAnswer(question.id, value);
            setGradeResult(result);
        } catch (e) {
            console.error(e);
            alert("评分失败，请稍后重试");
        } finally {
            setIsGrading(false);
        }
    };

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-brand-blue mb-2">
                简答题 · 第 {index} 题
            </p>
            <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
                {question.question}
            </p>

            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                placeholder="请输入你的答案..."
                className="w-full min-h-[120px] p-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-y"
            />

            <div className="mt-4 flex justify-end">
                {showAnswer && (
                    <button
                        onClick={handleGrade}
                        disabled={isGrading || !value.trim()}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 disabled:opacity-50 transition-colors font-medium"
                    >
                        {isGrading ? (
                            <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <Sparkles size={16} />
                        )}
                        AI 评分
                    </button>
                )}
            </div>

            {gradeResult && (
                <div className="mt-4 p-4 bg-indigo-50 rounded-xl border border-indigo-100">
                    <h4 className="font-bold text-indigo-900 mb-1 flex items-center gap-2">
                        <Sparkles size={16} />
                        AI 评分: {gradeResult.score}/10
                    </h4>
                    <p className="text-indigo-800 text-sm">{gradeResult.feedback}</p>
                </div>
            )}

            {showAnswer && (
                <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
                    <p className="font-semibold text-gray-900">参考答案：</p>
                    <p className="mt-1 text-gray-700">{question.answer}</p>
                    {question.explanation && (
                        <>
                            <p className="font-semibold text-gray-900 mt-3">解析：</p>
                            <p className="mt-1 whitespace-pre-line">{question.explanation}</p>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

export default ShortAnswerQuestionExam;
