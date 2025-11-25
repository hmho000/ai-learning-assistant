import type { ChapterStats } from "../../utils/quizStorage";

interface QuizSummaryProps {
  stats: ChapterStats | null;
}

const QuizSummary = ({ stats }: QuizSummaryProps) => {
  if (!stats || stats.totalAttempts === 0) {
    return (
      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-slate-500">
        本章节还没有作答记录。
      </div>
    );
  }

  const accuracy =
    stats.totalAttempts === 0
      ? 0
      : (stats.totalCorrect / stats.totalAttempts) * 100;

  return (
    <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-inner">
      <h3 className="text-lg font-semibold text-slate-800 mb-2">成绩统计</h3>
      <p className="text-slate-600">总作答次数：{stats.totalAttempts}</p>
      <p className="text-slate-600">总正确题数：{stats.totalCorrect}</p>
      <p className="text-slate-600">正确率：{accuracy.toFixed(1)}%</p>
    </div>
  );
};

export default QuizSummary;

