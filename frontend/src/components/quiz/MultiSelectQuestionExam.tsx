import { useMemo } from "react";
import type { MultipleChoiceQuestion } from "../../types/quiz";
import {
    extractOptionLetter,
    formatAnswerDisplay,
} from "../../utils/quizUtils";

interface MultiSelectQuestionExamProps {
    index: number;
    question: MultipleChoiceQuestion;
    value: string[]; // Array of selected labels
    onChange: (value: string[]) => void;
    disabled?: boolean;
    showAnswer?: boolean;
}

const MultiSelectQuestionExam = ({
    index,
    question,
    value = [],
    onChange,
    disabled = false,
    showAnswer = false,
}: MultiSelectQuestionExamProps) => {
    const options = Array.isArray(question.options) ? question.options : [];

    // Parse correct answers (e.g., "A,C" or ["A", "C"])
    const correctAnswers = useMemo(() => {
        if (Array.isArray(question.answer)) return question.answer;
        if (typeof question.answer === 'string') {
            // Try parsing JSON first
            try {
                const parsed = JSON.parse(question.answer);
                if (Array.isArray(parsed)) return parsed;
            } catch (e) {
                // Fallback to comma separation
                return question.answer.split(/[,，]/).map(s => s.trim().toUpperCase());
            }
        }
        return [];
    }, [question.answer]);

    const optionItems = useMemo(
        () =>
            options.map((opt, idx) => {
                const label = extractOptionLetter(opt, idx);
                return {
                    label: label,
                    text: opt.trim(),
                    isCorrectOption: correctAnswers.includes(label),
                };
            }),
        [options, correctAnswers]
    );

    const handleSelect = (label: string) => {
        if (disabled) return;
        if (value.includes(label)) {
            onChange(value.filter((v) => v !== label));
        } else {
            onChange([...value, label].sort());
        }
    };

    // Grading logic for display
    const isCorrect = value.length === correctAnswers.length && value.every(v => correctAnswers.includes(v));
    const isPartial = !isCorrect && value.length > 0 && value.every(v => correctAnswers.includes(v));
    const isWrong = !isCorrect && !isPartial;

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-brand-blue mb-2">
                多选题 · 第 {index} 题
            </p>
            <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
                {question.question}
            </p>

            <div className="space-y-3">
                {optionItems.map((option) => {
                    const isSelected = value.includes(option.label);
                    const optionIsCorrect = option.isCorrectOption;

                    let optionClasses =
                        "w-full text-left rounded-xl border px-4 py-3 transition focus:outline-none flex items-center";
                    if (!disabled) {
                        optionClasses += " hover:border-brand-blue/50 cursor-pointer";
                    }
                    if (isSelected) {
                        optionClasses += " ring-2 ring-brand-blue/50 border-brand-blue";
                    }

                    if (showAnswer) {
                        if (optionIsCorrect) {
                            optionClasses += " border-emerald-400 bg-emerald-50";
                        }
                        if (isSelected && !optionIsCorrect) {
                            optionClasses += " border-rose-400 bg-rose-50";
                        }
                        if (isSelected && optionIsCorrect) {
                            optionClasses += " border-emerald-500 bg-emerald-100";
                        }
                    }

                    return (
                        <button
                            key={option.label}
                            type="button"
                            className={optionClasses}
                            onClick={() => handleSelect(option.label)}
                            disabled={disabled}
                        >
                            <div className={`w-5 h-5 rounded border mr-3 flex items-center justify-center ${isSelected ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-300'}`}>
                                {isSelected && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>}
                            </div>
                            <span className="font-semibold mr-2">{option.label}.</span>
                            <span>{option.text.replace(/^([A-Z])[\.\)]\s*/i, "")}</span>
                        </button>
                    );
                })}
            </div>

            {showAnswer && (
                <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
                    <p
                        className={`font-semibold ${isCorrect ? "text-emerald-600" : isPartial ? "text-yellow-600" : "text-rose-600"
                            }`}
                    >
                        {isCorrect ? "回答正确！" : isPartial ? "回答不完整（得一半分）。" : "回答错误。"}
                    </p>
                    <p className="mt-1">
                        正确答案：{correctAnswers.join(", ")}
                    </p>
                    {question.explanation && (
                        <p className="mt-2 whitespace-pre-line">{question.explanation}</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default MultiSelectQuestionExam;
