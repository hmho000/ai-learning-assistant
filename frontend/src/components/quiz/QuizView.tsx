import { useEffect, useMemo, useState } from "react";
import type { QuizData } from "../../types/quiz";
import QuizSummary from "./QuizSummary";
import MultipleChoiceQuestion from "./MultipleChoiceQuestion";
import FillInBlankQuestion from "./FillInBlankQuestion";
import {
  getChapterStats,
  getWrongQuestions,
  type ChapterStats,
} from "../../utils/quizStorage";

interface QuizViewProps {
  courseId: string;
  chapterId: number;
  quizData: QuizData;
}

const QuizView = ({ courseId, chapterId, quizData }: QuizViewProps) => {
  const [stats, setStats] = useState<ChapterStats | null>(null);
  const [showWrongOnly, setShowWrongOnly] = useState(false);
  const [wrongKeys, setWrongKeys] = useState<string[]>([]);

  const chapterIndex = quizData?.meta?.chapter_index ?? chapterId ?? 1;

  useEffect(() => {
    refreshStats();
    setShowWrongOnly(false);
  }, [courseId, chapterId, quizData]);

  const refreshStats = () => {
    setStats(getChapterStats(courseId, chapterId));
    setWrongKeys(getWrongQuestions(courseId, chapterId));
  };

  const handleAnswered = () => {
    refreshStats();
  };

  const wrongSet = useMemo(() => new Set(wrongKeys), [wrongKeys]);

  const buildQuestionKey = (prefix: string, id: number) =>
    `${prefix}-${chapterIndex}-${id}`;

  const filterByWrong = <T extends { id: number }>(
    items: T[],
    prefix: string
  ) => {
    if (!showWrongOnly) {
      return items;
    }
    return items.filter((item) => wrongSet.has(buildQuestionKey(prefix, item.id)));
  };

  const filteredMultipleChoice = filterByWrong(
    quizData.multiple_choice || [],
    "mc"
  );
  const filteredFillIn = filterByWrong(quizData.fill_in_blank || [], "fb");

  const wrongToggleDisabled =
    !stats || stats.totalAttempts === 0 || wrongKeys.length === 0;

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-brand-blue">
            练习模式
          </p>
          <h2 className="text-2xl font-bold text-slate-900 mt-1">
            {quizData.meta?.quiz_title || "AI 练习题"}
          </h2>
          {quizData.meta?.quiz_description && (
            <p className="text-slate-600 mt-1">{quizData.meta.quiz_description}</p>
          )}
        </div>
        <div className="flex flex-col gap-3 md:flex-row">
          <button
            type="button"
            onClick={() => setShowWrongOnly((prev) => !prev)}
            disabled={wrongToggleDisabled}
            className={`rounded-xl px-5 py-2 text-sm font-semibold transition ${
              showWrongOnly
                ? "bg-brand-blue text-white shadow"
                : "border border-slate-300 text-slate-700"
            } ${wrongToggleDisabled ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            {showWrongOnly ? "显示全部题目" : "只看错题/薄弱题"}
          </button>
          <button
            type="button"
            onClick={refreshStats}
            className="rounded-xl border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-700 hover:border-brand-blue/60"
          >
            刷新统计
          </button>
        </div>
      </div>

      {showWrongOnly && !wrongKeys.length && (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center text-slate-600">
          暂无错题记录，先去做几道题吧！
        </div>
      )}

      {filteredMultipleChoice.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-900">一、选择题</h3>
          {filteredMultipleChoice.map((item) => (
            <MultipleChoiceQuestion
              key={`mc-${item.id}`}
              courseId={courseId}
              chapterId={chapterId}
              question={item}
              questionKey={buildQuestionKey("mc", item.id)}
              onAnswered={handleAnswered}
            />
          ))}
        </div>
      )}

      {filteredFillIn.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-900">二、填空题</h3>
          {filteredFillIn.map((item) => (
            <FillInBlankQuestion
              key={`fb-${item.id}`}
              courseId={courseId}
              chapterId={chapterId}
              question={item}
              questionKey={buildQuestionKey("fb", item.id)}
              onAnswered={handleAnswered}
            />
          ))}
        </div>
      )}

      {!filteredMultipleChoice.length && !filteredFillIn.length && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 p-6 text-center text-slate-500">
          当前筛选条件下没有题目，先切换到“显示全部题目”再试试吧。
        </div>
      )}

      <QuizSummary stats={stats} />
    </section>
  );
};

export default QuizView;

