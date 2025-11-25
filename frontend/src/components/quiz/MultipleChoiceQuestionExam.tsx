import { useMemo } from "react";
import type { MultipleChoiceQuestion } from "../../types/quiz";
import {
  extractOptionLetter,
  isChoiceCorrect,
  formatAnswerDisplay,
  extractAnswerLetter,
} from "../../utils/quizUtils";

interface MultipleChoiceQuestionExamProps {
  index: number;
  question: MultipleChoiceQuestion;
  value: string | string[];
  onChange: (value: string | string[]) => void;
  disabled?: boolean;
  showAnswer?: boolean;
}

const MultipleChoiceQuestionExam = ({
  index,
  question,
  value,
  onChange,
  disabled = false,
  showAnswer = false,
}: MultipleChoiceQuestionExamProps) => {
  const options = Array.isArray(question.options) ? question.options : [];

  const answerLetter = useMemo(
    () => extractAnswerLetter(question.answer),
    [question.answer]
  );

  const optionItems = useMemo(
    () =>
      options.map((opt, idx) => ({
        label: extractOptionLetter(opt, idx),
        text: opt.trim(),
        isCorrectOption: isChoiceCorrect(opt, idx, question.answer),
      })),
    [options, question.answer]
  );

  const handleSelect = (label: string) => {
    if (disabled) return;
    onChange(label);
  };

  const selectedValue = Array.isArray(value) ? value[0] : value;
  const correctLabel =
    optionItems.find((item) => item.isCorrectOption)?.label || answerLetter;
  const isSelectedCorrect = selectedValue
    ? optionItems.find((item) => item.label === selectedValue)?.isCorrectOption
    : false;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-semibold text-brand-blue mb-2">
        选择题 · 第 {index} 题
      </p>
      <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
        {question.question}
      </p>

      <div className="space-y-3">
        {optionItems.map((option) => {
          const isSelected = selectedValue === option.label;
          const optionIsCorrect = option.isCorrectOption;

          let optionClasses =
            "w-full text-left rounded-xl border px-4 py-3 transition focus:outline-none";
          if (!disabled) {
            optionClasses += " hover:border-brand-blue/50 cursor-pointer";
          }
          if (isSelected) {
            optionClasses += " ring-2 ring-brand-blue/50";
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
              <span className="font-semibold mr-2">{option.label}.</span>
              <span>{option.text.replace(/^([A-Z])[\.\)]\s*/i, "")}</span>
            </button>
          );
        })}
      </div>

      {showAnswer && (
        <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          <p
            className={`font-semibold ${
              isSelectedCorrect ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {isSelectedCorrect ? "回答正确！" : "回答错误。"}
          </p>
          <p className="mt-1">
            正确答案：{formatAnswerDisplay(question.answer)}{" "}
            {correctLabel ? `(选项 ${correctLabel})` : ""}
          </p>
          {question.explanation && (
            <p className="mt-2 whitespace-pre-line">{question.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default MultipleChoiceQuestionExam;

