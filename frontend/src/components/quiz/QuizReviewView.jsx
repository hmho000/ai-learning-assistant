import React, { useState } from 'react';
import { CheckCircle, XCircle, HelpCircle, Brain, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { gradeShortAnswer, reviewCode } from '../../api';
import CodingQuestion from '../CodingQuestion';
import Editor from '@monaco-editor/react';

const QuestionGroup = ({ title, questions, renderQuestion }) => {
    if (!questions || questions.length === 0) return null;
    return (
        <div className="space-y-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 border-l-4 border-blue-500 pl-3">{title}</h3>
            {questions.map((q, index) => renderQuestion(q, index))}
        </div>
    );
};

const QuizReviewView = ({ quiz, onStartExam }) => {
    const [gradingLoading, setGradingLoading] = useState({});
    const [gradingResult, setGradingResult] = useState({});
    const [userInputs, setUserInputs] = useState({}); // 在看题模式下存储用户输入以进行评分

    if (!quiz || !quiz.questions) return null;

    // 按类型分组题目
    const groupedQuestions = {
        multiple_choice: quiz.questions.filter(q => q.type === 'multiple_choice'),
        multi_select: quiz.questions.filter(q => q.type === 'multi_select'),
        true_false: quiz.questions.filter(q => q.type === 'true_false'),
        fill_in_blank: quiz.questions.filter(q => q.type === 'fill_in_blank'),
        short_answer: quiz.questions.filter(q => q.type === 'short_answer'),
        coding: quiz.questions.filter(q => q.type === 'coding'),
    };

    const handleGrade = async (q) => {
        const input = userInputs[q.id];
        if (!input) {
            alert("请输入内容后再评分");
            return;
        }

        setGradingLoading(prev => ({ ...prev, [q.id]: true }));
        try {
            let res;
            if (q.type === 'short_answer') {
                res = await gradeShortAnswer(q.id, input);
            } else if (q.type === 'coding') {
                res = await reviewCode(q.id, input);
            }
            setGradingResult(prev => ({ ...prev, [q.id]: res }));
        } catch (error) {
            console.error("Grading failed:", error);
            alert("评分失败，请重试");
        } finally {
            setGradingLoading(prev => ({ ...prev, [q.id]: false }));
        }
    };

    const renderQuestionBase = (q, index, content) => (
        <div key={q.id || index} className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blue-50 text-blue-600 font-bold rounded-full">
                    {index + 1}
                </span>
                <div className="flex-1">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">{q.stem}</h4>
                    {content}
                    {/* 解析 */}
                    <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="flex items-start gap-2 text-sm text-gray-600">
                            <HelpCircle className="w-4 h-4 mt-0.5 text-blue-500 flex-shrink-0" />
                            <div>
                                <span className="font-semibold text-gray-900">解析：</span>
                                <div className="mt-1 text-gray-700 leading-relaxed whitespace-pre-wrap">
                                    {q.explanation || "暂无解析"}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderOptions = (q, type) => {
        let options = [];
        try {
            if (Array.isArray(q.options)) {
                options = q.options;
            } else if (q.options_json) {
                options = JSON.parse(q.options_json);
            }
        } catch (e) {
            return <div className="text-red-500">选项解析错误</div>;
        }

        // 解析多选题答案
        let correctAnswers = [];
        if (type === 'multi_select') {
            try {
                correctAnswers = Array.isArray(q.answer) ? q.answer : JSON.parse(q.answer);
            } catch (e) {
                // 如果答案只是字符串但应该是数组，则进行回退
                correctAnswers = [q.answer];
            }
        } else {
            correctAnswers = [q.answer];
        }

        return (
            <div className="space-y-3 mb-6">
                {options.map((opt, i) => {
                    const letter = ["A", "B", "C", "D", "E", "F"][i];
                    const isCorrect = correctAnswers.includes(letter) || correctAnswers.includes(i); // 支持字母或索引

                    return (
                        <div
                            key={i}
                            className={`relative p-4 rounded-xl border-2 transition-all duration-200 ${isCorrect
                                ? "bg-green-50 border-green-500 text-green-800 shadow-sm"
                                : "bg-white border-gray-100 text-gray-600"
                                }`}
                        >
                            <div className="flex items-start gap-3">
                                <span className={`flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full text-sm font-bold border ${isCorrect
                                    ? "bg-green-500 text-white border-green-500"
                                    : "bg-gray-100 text-gray-500 border-gray-200"
                                    }`}>
                                    {letter}
                                </span>
                                <span className="text-base leading-relaxed">{opt}</span>
                                {isCorrect && (
                                    <CheckCircle className="absolute right-4 top-4 w-5 h-5 text-green-500" />
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    const renderTrueFalse = (q) => {
        const isTrue = String(q.answer).toLowerCase() === 'true';
        return (
            <div className="flex gap-4 mb-6">
                <div className={`flex-1 p-4 rounded-xl border-2 flex items-center justify-center gap-2 ${isTrue
                    ? "bg-green-50 border-green-500 text-green-700"
                    : "bg-gray-50 border-gray-200 text-gray-400"
                    }`}>
                    <CheckCircle size={20} /> 正确
                </div>
                <div className={`flex-1 p-4 rounded-xl border-2 flex items-center justify-center gap-2 ${!isTrue
                    ? "bg-green-50 border-green-500 text-green-700"
                    : "bg-gray-50 border-gray-200 text-gray-400"
                    }`}>
                    <XCircle size={20} /> 错误
                </div>
            </div>
        );
    };

    const renderFillInBlank = (q) => (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            <span className="font-semibold mr-2">正确答案：</span>
            {q.answer}
        </div>
    );

    const renderTextWithGrading = (q, placeholder) => {
        const isCoding = q.type === 'coding';

        return (
            <div className="space-y-4 mb-6">
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
                    <div className="font-semibold mb-2">参考答案：</div>
                    {isCoding ? (
                        <div className="rounded-lg overflow-hidden border border-green-200 bg-white">
                            <Editor
                                height="200px"
                                language="python"
                                theme="vs-light"
                                value={q.answer}
                                options={{
                                    readOnly: true,
                                    minimap: { enabled: false },
                                    fontSize: 13,
                                    lineNumbers: 'on',
                                    scrollBeyondLastLine: false,
                                    automaticLayout: true,
                                    wordWrap: 'on'
                                }}
                            />
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap">
                            {q.answer}
                        </div>
                    )}
                </div>

                {/* 评分部分 */}
                <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                    <h5 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                        <Brain size={18} /> AI 评分体验
                    </h5>

                    {isCoding ? (
                        <div className="mb-3">
                            <CodingQuestion
                                question={q}
                                value={userInputs[q.id] || ""}
                                onChange={(val) => setUserInputs(prev => ({ ...prev, [q.id]: val }))}
                                onReview={reviewCode}
                                showReviewButton={true}
                            />
                        </div>
                    ) : (
                        <>
                            <textarea
                                className="w-full p-3 rounded-lg border border-blue-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[100px] mb-3"
                                placeholder={placeholder}
                                value={userInputs[q.id] || ""}
                                onChange={(e) => setUserInputs(prev => ({ ...prev, [q.id]: e.target.value }))}
                            />

                            <button
                                onClick={() => handleGrade(q)}
                                disabled={gradingLoading[q.id]}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
                            >
                                {gradingLoading[q.id] ? <Loader2 className="animate-spin" size={16} /> : <Brain size={16} />}
                                开始评分
                            </button>

                            {gradingResult[q.id] && (
                                <div className="mt-4 bg-white rounded-lg p-5 border border-blue-100 shadow-sm animate-in fade-in slide-in-from-top-2">
                                    <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-50">
                                        <span className="font-bold text-gray-900 flex items-center gap-2">
                                            <CheckCircle className="text-green-500" size={18} />
                                            评分结果
                                        </span>
                                        <span className="text-2xl font-bold text-blue-600">
                                            {gradingResult[q.id].score}
                                            <span className="text-sm text-gray-400 ml-1 font-normal">/ 10</span>
                                        </span>
                                    </div>
                                    <div className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap bg-gray-50 p-3 rounded-lg border border-gray-100">
                                        {gradingResult[q.id].feedback}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        );
    };

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

            {(() => {
                let sectionIndex = 0;
                const renderGroup = (title, questions, renderFn) => {
                    if (!questions || questions.length === 0) return null;
                    sectionIndex++;
                    const chineseNumbers = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"];
                    const fullTitle = `${chineseNumbers[sectionIndex - 1]}、${title}`;

                    return (
                        <QuestionGroup
                            key={title}
                            title={fullTitle}
                            questions={questions}
                            renderQuestion={renderFn}
                        />
                    );
                };

                return (
                    <>
                        {renderGroup("单选题", groupedQuestions.multiple_choice, (q, i) => renderQuestionBase(q, i, renderOptions(q, 'multiple_choice')))}
                        {renderGroup("多选题", groupedQuestions.multi_select, (q, i) => renderQuestionBase(q, i, renderOptions(q, 'multi_select')))}
                        {renderGroup("判断题", groupedQuestions.true_false, (q, i) => renderQuestionBase(q, i, renderTrueFalse(q)))}
                        {renderGroup("填空题", groupedQuestions.fill_in_blank, (q, i) => renderQuestionBase(q, i, renderFillInBlank(q)))}
                        {renderGroup("简答题", groupedQuestions.short_answer, (q, i) => renderQuestionBase(q, i, renderTextWithGrading(q, "输入你的答案尝试 AI 评分...")))}
                        {renderGroup("代码题", groupedQuestions.coding, (q, i) => renderQuestionBase(q, i, renderTextWithGrading(q, "粘贴你的代码尝试 AI 评分...")))}
                    </>
                );
            })()}

            <div className="flex justify-center pt-8 pb-12">
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
