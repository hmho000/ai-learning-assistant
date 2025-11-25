import React, { useState } from "react";
import { QuizData, UserAnswer } from "../../types/quiz";
import MultipleChoiceQuestionExam from "./MultipleChoiceQuestionExam";
import FillInBlankQuestionExam from "./FillInBlankQuestionExam";
import QuizExamSummary from "./QuizExamSummary";
import { saveQuizResult } from "../../utils/quizStorage";
import { calcScore } from "../../utils/quizUtils";

interface QuizExamViewProps {
  quiz: QuizData;
  chapterId: number;
  courseId?: string;
}

const QuizExamView: React.FC<QuizExamViewProps> = ({
  quiz,
  chapterId,
  courseId,
}) => {
  const [answers, setAnswers] = useState<UserAnswer[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [scoreResult, setScoreResult] = useState<ReturnType<typeof calcScore> | null>(null);

  const { multiple_choice, fill_in_blank } = quiz;

  const handleAnswerChange = (questionId: string, value: string | string[]) => {
    setAnswers((prev) => {
      const idx = prev.findIndex((a) => a.questionId === questionId);
      if (idx === -1) {
        return [...prev, { questionId, value }];
      }
      const copy = [...prev];
      copy[idx] = { questionId, value };
      return copy;
    });
  };

  const handleSubmit = () => {
    const result = calcScore(quiz, answers);
    setScore(result.score);
    setScoreResult(result);
    setSubmitted(true);

    saveQuizResult({
      courseId: courseId ?? "default-course",
      chapterId,
      score: result.score,
      total: result.total,
      timestamp: Date.now(),
      answers,
      detail: result.detail,
    });
  };

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold mb-2">一、选择题</h2>
        {multiple_choice.map((q, index) => (
          <MultipleChoiceQuestionExam
            key={q.id}
            index={index + 1}
            question={q}
            value={answers.find((a) => a.questionId === `mc-${q.id}`)?.value ?? ""}
            onChange={(value) => handleAnswerChange(`mc-${q.id}`, value)}
            disabled={submitted}
            showAnswer={submitted}
          />
        ))}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">二、填空题</h2>
        {fill_in_blank.map((q, index) => (
          <FillInBlankQuestionExam
            key={q.id}
            index={index + 1}
            question={q}
            value={
              (answers.find((a) => a.questionId === `fb-${q.id}`)?.value as string) ?? ""
            }
            onChange={(value) => handleAnswerChange(`fb-${q.id}`, value)}
            disabled={submitted}
            showAnswer={submitted}
          />
        ))}
      </section>

      <div className="flex gap-4 items-center">
        {!submitted && (
          <button
            className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600 transition"
            onClick={handleSubmit}
          >
            提交答案
          </button>
        )}
        {submitted && score !== null && (
          <span className="text-lg font-semibold text-brand-blue">
            本次得分：{score} / {scoreResult?.total ?? 0}
          </span>
        )}
      </div>

      {submitted && scoreResult && (
        <QuizExamSummary
          quiz={quiz}
          answers={answers}
          score={score ?? 0}
          scoreResult={scoreResult}
        />
      )}
    </div>
  );
};

export default QuizExamView;

