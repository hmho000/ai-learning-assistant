import { useMemo, useState } from "react";
import type { MultipleChoiceQuestion as MCQuestion } from "../../types/quiz";
import {
  extractOptionLetter,
  isChoiceCorrect,
  formatAnswerDisplay,
  extractAnswerLetter,
} from "../../utils/quizUtils";
import { updateQuestionStat } from "../../utils/quizStorage";

interface MCQuestionProps {
  courseId: string;
  chapterId: number;
  question: MCQuestion;
  questionKey: string;
  onAnswered?: (result: { correct: boolean }) => void;
}

const MultipleChoiceQuestion = ({
  courseId,
  chapterId,
  question,
  questionKey,
  onAnswered,
}: MCQuestionProps) => {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

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

  const handleSelect = (label: string, optionIndex: number, optionText: string) => {
    setSelectedKey(label);
    const correct = isChoiceCorrect(optionText, optionIndex, question.answer);
    setIsCorrect(correct);
    setShowExplanation(true);
    updateQuestionStat(courseId, chapterId, questionKey, correct);
    onAnswered?.({ correct });
  };

  const answered = selectedKey !== null;
  const correctLabel =
    optionItems.find((item) => item.isCorrectOption)?.label || answerLetter;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-semibold text-brand-blue mb-2">
        选择题 · 第 {question.id} 题
      </p>
      <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
        {question.question}
      </p>

      <div className="space-y-3">
        {optionItems.map((option, idx) => {
          const isSelected = selectedKey === option.label;
          const optionIsCorrect = option.isCorrectOption;

          let optionClasses =
            "w-full text-left rounded-xl border px-4 py-3 transition focus:outline-none";
          optionClasses += isSelected ? " ring-2 ring-brand-blue/50" : "";
          optionClasses += " hover:border-brand-blue/50";

          if (answered) {
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
              onClick={() => handleSelect(option.label, idx, option.text)}
            >
              <span className="font-semibold mr-2">{option.label}.</span>
              <span>{option.text.replace(/^([A-Z])[\.\)]\s*/i, "")}</span>
            </button>
          );
        })}
      </div>

      {showExplanation && (
        <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          <p
            className={`font-semibold ${
              isCorrect ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {isCorrect ? "回答正确！" : "回答错误。"}
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

export default MultipleChoiceQuestion;

