import { useMemo } from "react";
import type { MultipleChoiceQuestion } from "../../types/quiz";
import { formatAnswerDisplay } from "../../utils/quizUtils";

interface TrueFalseQuestionExamProps {
    index: number;
    question: MultipleChoiceQuestion;
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
    showAnswer?: boolean;
}

const TrueFalseQuestionExam = ({
    index,
    question,
    value,
    onChange,
    disabled = false,
    showAnswer = false,
}: TrueFalseQuestionExamProps) => {

    // Normalize answer to boolean string "True" or "False"
    const correctAnswer = useMemo(() => {
        const ans = String(question.answer).toLowerCase();
        if (ans === 'true' || ans === 't' || ans === 'yes' || ans === '正确') return "True";
        return "False";
    }, [question.answer]);

    const handleSelect = (val: string) => {
        if (disabled) return;
        onChange(val);
    };

    const isCorrect = value === correctAnswer;

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-brand-blue mb-2">
                判断题 · 第 {index} 题
            </p>
            <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
                {question.question}
            </p>

            <div className="flex gap-4">
                {["True", "False"].map((option) => {
                    const isSelected = value === option;
                    const optionLabel = option === "True" ? "正确" : "错误";

                    let optionClasses =
                        "flex-1 rounded-xl border px-4 py-3 transition focus:outline-none text-center font-medium";
                    if (!disabled) {
                        optionClasses += " hover:border-brand-blue/50 cursor-pointer";
                    }
                    if (isSelected) {
                        optionClasses += " ring-2 ring-brand-blue/50 border-brand-blue bg-blue-50 text-blue-700";
                    } else {
                        optionClasses += " bg-white text-gray-700";
                    }

                    if (showAnswer) {
                        if (option === correctAnswer) {
                            optionClasses += " border-emerald-400 bg-emerald-50 ring-emerald-200";
                        } else if (isSelected && option !== correctAnswer) {
                            optionClasses += " border-rose-400 bg-rose-50 ring-rose-200";
                        }
                    }

                    return (
                        <button
                            key={option}
                            type="button"
                            className={optionClasses}
                            onClick={() => handleSelect(option)}
                            disabled={disabled}
                        >
                            {optionLabel}
                        </button>
                    );
                })}
            </div>

            {showAnswer && (
                <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
                    <p
                        className={`font-semibold ${isCorrect ? "text-emerald-600" : "text-rose-600"
                            }`}
                    >
                        {isCorrect ? "回答正确！" : "回答错误。"}
                    </p>
                    <p className="mt-1">
                        正确答案：{correctAnswer === "True" ? "正确" : "错误"}
                    </p>
                    {question.explanation && (
                        <p className="mt-2 whitespace-pre-line">{question.explanation}</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default TrueFalseQuestionExam;
