import type { QuizData, UserAnswer, ScoreResult } from "../../types/quiz";

interface QuizExamSummaryProps {
  quiz: QuizData;
  answers: UserAnswer[];
  score: number;
  scoreResult: ScoreResult;
}

const QuizExamSummary = ({
  quiz,
  answers,
  score,
  scoreResult,
}: QuizExamSummaryProps) => {
  const total = scoreResult.total;
  const percentage = total > 0 ? ((score / total) * 100).toFixed(1) : "0.0";

  const correctDetail = scoreResult.detail.filter((d) => d.correct);
  const wrongDetail = scoreResult.detail.filter((d) => !d.correct);

  return (
    <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-inner">
      <h3 className="text-lg font-semibold text-slate-800 mb-4">答题结果</h3>
      <div className="mb-4">
        <p className="text-2xl font-bold text-brand-blue">
          得分：{score} / {total}
        </p>
        <p className="text-slate-600 mt-1">正确率：{percentage}%</p>
      </div>

      {wrongDetail.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-semibold text-rose-600 mb-2">
            错题 ({wrongDetail.length} 道)：
          </p>
          <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
            {wrongDetail.map((detail) => {
              const questionId = detail.questionId;
              const isMC = questionId.startsWith("mc-");
              const question = isMC
                ? quiz.multiple_choice.find(
                    (q) => `mc-${q.id}` === questionId
                  )
                : quiz.fill_in_blank.find((q) => `fb-${q.id}` === questionId);

              if (!question) return null;

              return (
                <li key={questionId}>
                  {isMC ? "选择题" : "填空题"} 第 {question.id} 题
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {correctDetail.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-semibold text-emerald-600 mb-2">
            正确题 ({correctDetail.length} 道)：
          </p>
          <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
            {correctDetail.map((detail) => {
              const questionId = detail.questionId;
              const isMC = questionId.startsWith("mc-");
              const question = isMC
                ? quiz.multiple_choice.find(
                    (q) => `mc-${q.id}` === questionId
                  )
                : quiz.fill_in_blank.find((q) => `fb-${q.id}` === questionId);

              if (!question) return null;

              return (
                <li key={questionId}>
                  {isMC ? "选择题" : "填空题"} 第 {question.id} 题
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
};

export default QuizExamSummary;

