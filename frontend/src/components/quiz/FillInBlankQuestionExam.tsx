import type { FillInBlankQuestion } from "../../types/quiz";
import { checkFillBlank, formatAnswerDisplay } from "../../utils/quizUtils";

interface FillInBlankQuestionExamProps {
  index: number;
  question: FillInBlankQuestion;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  showAnswer?: boolean;
}

const FillInBlankQuestionExam = ({
  index,
  question,
  value,
  onChange,
  disabled = false,
  showAnswer = false,
}: FillInBlankQuestionExamProps) => {
  const isCorrect = value ? checkFillBlank(value, question.answer) : false;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-semibold text-brand-blue mb-2">
        填空题 · 第 {index} 题
      </p>
      <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
        {question.question}
      </p>

      <div className="flex flex-col gap-3">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="请输入答案"
          disabled={disabled}
          className="rounded-xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/40 disabled:opacity-50 disabled:cursor-not-allowed"
        />
      </div>

      {showAnswer && (
        <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          <p
            className={`font-semibold ${
              isCorrect ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {isCorrect ? "回答正确！" : "回答错误。"}
          </p>
          <p className="mt-1">标准答案：{formatAnswerDisplay(question.answer)}</p>
          {question.explanation && (
            <p className="mt-2 whitespace-pre-line">{question.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default FillInBlankQuestionExam;

