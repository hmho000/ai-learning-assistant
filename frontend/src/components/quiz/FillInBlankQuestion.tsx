import { useState } from "react";
import type { FillInBlankQuestion as FBQuestion } from "../../types/quiz";
import { checkFillBlank, formatAnswerDisplay } from "../../utils/quizUtils";
import { updateQuestionStat } from "../../utils/quizStorage";

interface FillBlankQuestionProps {
  courseId: string;
  chapterId: number;
  question: FBQuestion;
  questionKey: string;
  onAnswered?: (result: { correct: boolean }) => void;
}

const FillInBlankQuestion = ({
  courseId,
  chapterId,
  question,
  questionKey,
  onAnswered,
}: FillBlankQuestionProps) => {
  const [inputValue, setInputValue] = useState("");
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleSubmit = () => {
    const correct = checkFillBlank(inputValue, question.answer);
    setIsCorrect(correct);
    setShowExplanation(true);
    updateQuestionStat(courseId, chapterId, questionKey, correct);
    onAnswered?.({ correct });
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-semibold text-brand-blue mb-2">
        填空题 · 第 {question.id} 题
      </p>
      <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
        {question.question}
      </p>

      <div className="flex flex-col gap-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="请输入答案"
          className="rounded-xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/40"
        />
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleSubmit}
            className="rounded-xl bg-brand-blue px-5 py-2 text-white shadow hover:bg-brand-blue/90"
          >
            提交答案
          </button>
          <button
            type="button"
            onClick={() => setShowExplanation((prev) => !prev)}
            className="rounded-xl border border-slate-300 px-5 py-2 text-slate-700 hover:border-brand-blue/60"
          >
            {showExplanation ? "隐藏解析" : "查看解析"}
          </button>
        </div>
      </div>

      {showExplanation && (
        <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          {isCorrect !== null && (
            <p
              className={`font-semibold ${
                isCorrect ? "text-emerald-600" : "text-rose-600"
              }`}
            >
              {isCorrect ? "回答正确！" : "回答错误。"}
            </p>
          )}
          <p className="mt-1">标准答案：{formatAnswerDisplay(question.answer)}</p>
          {question.explanation && (
            <p className="mt-2 whitespace-pre-line">{question.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default FillInBlankQuestion;

