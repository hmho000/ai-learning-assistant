import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { MessageSquare, CheckCircle, AlertCircle } from 'lucide-react';

const CodingQuestion = ({ question, onReview, value, onChange, readOnly = false, showReviewButton = true }) => {
    // 如果提供了 value，则使用它（受控），否则使用内部状态（非受控 - 回退）
    // 但对于 ExamView，我们需要受控组件。
    const [internalCode, setInternalCode] = useState(question.answer || "// 在此处编写代码\n");

    const code = value !== undefined ? value : internalCode;

    const handleChange = (val) => {
        if (onChange) {
            onChange(val);
        } else {
            setInternalCode(val);
        }
    };

    const [reviewResult, setReviewResult] = useState(null);
    const [isReviewing, setIsReviewing] = useState(false);

    const handleReview = async () => {
        setIsReviewing(true);
        try {
            // 调用父处理程序，该处理程序调用后端 API
            const result = await onReview(question.id, code);
            setReviewResult(result);
        } catch (error) {
            console.error("Review failed", error);
            setReviewResult({ error: "评审请求失败，请稍后重试。" });
        } finally {
            setIsReviewing(false);
        }
    };

    return (
        <div className="space-y-4">
            <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700 shadow-lg">
                <div className="bg-gray-800 px-4 py-2 flex justify-between items-center border-b border-gray-700">
                    <span className="text-gray-300 text-sm font-mono">Python 3.10</span>
                    <span className="text-xs text-gray-500">Monaco Editor</span>
                </div>
                <Editor
                    height="300px"
                    defaultLanguage="python"
                    theme="vs-dark"
                    value={code}
                    onChange={handleChange}
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        readOnly: readOnly,
                    }}
                />
            </div>

            <div className="flex justify-end gap-3">
                {showReviewButton && (
                    <button
                        onClick={handleReview}
                        disabled={isReviewing}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                    >
                        {isReviewing ? (
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <MessageSquare size={18} />
                        )}
                        AI 代码评审
                    </button>
                )}
            </div>

            {reviewResult && (
                <div className={`p-4 rounded-lg border ${reviewResult.error ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                    <h4 className={`font-bold flex items-center gap-2 mb-2 ${reviewResult.error ? 'text-red-800' : 'text-green-800'}`}>
                        {reviewResult.error ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
                        {reviewResult.error ? "评审出错" : "评审结果"}
                    </h4>
                    {reviewResult.error ? (
                        <p className="text-red-700">{reviewResult.error}</p>
                    ) : (
                        <div className="prose prose-sm max-w-none text-gray-700">
                            <p><strong>评分:</strong> {reviewResult.score}/10</p>
                            <div className="whitespace-pre-wrap">{reviewResult.feedback}</div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default CodingQuestion;
