import React from 'react';
import { CheckCircle, XCircle, HelpCircle } from 'lucide-react';

const QuizReviewView = ({ quiz, onStartExam }) => {
    if (!quiz || !quiz.questions) return null;

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center border-b pb-4">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">{quiz.title}</h2>
                    <p className="text-gray-500 mt-1">看题模式：包含答案与解析</p>
                </div>
                <button
                    onClick={onStartExam}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
                >
                    开始答题模式
                </button>
            </div>

            <div className="space-y-6">
                {quiz.questions.map((q, index) => (
                    <div key={q.id || index} className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start gap-3">
                            <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blue-50 text-blue-600 font-bold rounded-full">
                                {index + 1}
                            </span>
                            <div className="flex-1">
                                <h3 className="text-lg font-medium text-gray-900 mb-4">{q.stem}</h3>

                                {/* Options */}
                                {['multiple_choice', 'single_choice'].includes(q.type) && (
                                    <div className="space-y-3 mb-6">
                                        {(() => {
                                            try {
                                                let options = [];
                                                if (Array.isArray(q.options)) {
                                                    options = q.options;
                                                } else if (q.options_json) {
                                                    options = JSON.parse(q.options_json);
                                                }

                                                return options.map((opt, i) => {
                                                    // Determine if this option is the correct answer
                                                    // Support both index-based (0, 1, 2...) and letter-based (A, B, C...) answers
                                                    const isAnswer = String(i) === String(q.answer) || ["A", "B", "C", "D"][i] === q.answer;

                                                    return (
                                                        <div
                                                            key={i}
                                                            className={`relative p-4 rounded-xl border-2 transition-all duration-200 ${isAnswer
                                                                ? "bg-green-50 border-green-500 text-green-800 shadow-sm"
                                                                : "bg-white border-gray-100 text-gray-600 hover:border-gray-200"
                                                                }`}
                                                        >
                                                            <div className="flex items-start gap-3">
                                                                <span className={`flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full text-sm font-bold border ${isAnswer
                                                                    ? "bg-green-500 text-white border-green-500"
                                                                    : "bg-gray-100 text-gray-500 border-gray-200"
                                                                    }`}>
                                                                    {["A", "B", "C", "D"][i]}
                                                                </span>
                                                                <span className="text-base leading-relaxed">{opt}</span>
                                                                {isAnswer && (
                                                                    <CheckCircle className="absolute right-4 top-4 w-5 h-5 text-green-500" />
                                                                )}
                                                            </div>
                                                        </div>
                                                    );
                                                });
                                            } catch (e) {
                                                console.error("Error parsing options:", e);
                                                return <div className="text-red-500 text-sm">题目选项解析错误</div>;
                                            }
                                        })()}
                                    </div>
                                )}

                                {/* Fill in blank answer display */}
                                {q.type === 'fill_in_blank' && (
                                    <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-800">
                                        <span className="font-semibold mr-2">答案：</span>
                                        {q.answer}
                                    </div>
                                )}

                                {/* Explanation */}
                                <div className="mt-4 pt-4 border-t border-gray-100">
                                    <div className="flex items-start gap-2 text-sm text-gray-600">
                                        <HelpCircle className="w-4 h-4 mt-0.5 text-blue-500" />
                                        <div>
                                            <span className="font-semibold text-gray-900">解析：</span>
                                            {q.explanation || "暂无解析"}
                                        </div>
                                    </div>
                                </div>

                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="flex justify-center pt-8">
                <button
                    onClick={onStartExam}
                    className="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                >
                    准备好了，开始答题！
                </button>
            </div>
        </div>
    );
};

export default QuizReviewView;
