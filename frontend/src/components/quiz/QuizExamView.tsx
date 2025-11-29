import React, { useState, useMemo } from "react";
import { UserAnswer } from "../../types/quiz";
import MultipleChoiceQuestionExam from "./MultipleChoiceQuestionExam";
import FillInBlankQuestionExam from "./FillInBlankQuestionExam";
import QuizExamSummary from "./QuizExamSummary";
import { saveQuizResult } from "../../utils/quizStorage";
import { calcScore } from "../../utils/quizUtils";

// Define local interfaces for the API data structure if not imported
interface Question {
  id: number;
  type: string;
  stem: string;
  options_json?: string;
  answer: string;
  explanation?: string;
}

interface QuizData {
  title: string;
  questions: Question[];
}

interface QuizExamViewProps {
  quiz: QuizData;
  chapterId: number;
  courseId?: number;
}

const QuizExamView: React.FC<QuizExamViewProps> = ({
  quiz,
  chapterId,
  courseId,
}) => {
  const [answers, setAnswers] = useState<UserAnswer[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [scoreResult, setScoreResult] = useState<any>(null);

  // Filter questions by type
  const multipleChoiceQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "multiple_choice"),
    [quiz.questions]);

  const fillInBlankQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "fill_in_blank"),
    [quiz.questions]);

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
    // Need to adapt calcScore to handle this structure or adapt the structure to calcScore
    // For simplicity, let's adapt the structure to match what calcScore expects (legacy)
    const legacyQuizFormat = {
      title: quiz.title,
      multiple_choice: multipleChoiceQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        options: q.options_json ? JSON.parse(q.options_json) : [],
        answer: q.answer,
        explanation: q.explanation
      })),
      fill_in_blank: fillInBlankQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        answer: q.answer,
        explanation: q.explanation
      }))
    };

    const result = calcScore(legacyQuizFormat, answers);
    setScore(result.score);
    setScoreResult(result);
    setSubmitted(true);

    saveQuizResult({
      courseId: courseId ? String(courseId) : "default-course",
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
      {multipleChoiceQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">一、选择题</h2>
          {multipleChoiceQuestions.map((q, index) => {
            const options = q.options_json ? JSON.parse(q.options_json) : [];
            // Adapt to component props
            const qProps = {
              id: q.id,
              question: q.stem,
              options: options,
              answer: q.answer,
              explanation: q.explanation
            };

            return (
              <MultipleChoiceQuestionExam
                key={q.id}
                index={index + 1}
                question={qProps}
                value={answers.find((a) => a.questionId === `mc-${q.id}`)?.value ?? ""}
                onChange={(value) => handleAnswerChange(`mc-${q.id}`, value)}
                disabled={submitted}
                showAnswer={submitted}
              />
            );
          })}
        </section>
      )}

      {fillInBlankQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">二、填空题</h2>
          {fillInBlankQuestions.map((q, index) => {
            const qProps = {
              id: q.id,
              question: q.stem,
              answer: q.answer,
              explanation: q.explanation
            };

            return (
              <FillInBlankQuestionExam
                key={q.id}
                index={index + 1}
                question={qProps}
                value={
                  (answers.find((a) => a.questionId === `fb-${q.id}`)?.value as string) ?? ""
                }
                onChange={(value) => handleAnswerChange(`fb-${q.id}`, value)}
                disabled={submitted}
                showAnswer={submitted}
              />
            );
          })}
        </section>
      )}

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
          quiz={{
            title: quiz.title,
            multiple_choice: multipleChoiceQuestions.map(q => ({
              id: q.id,
              question: q.stem,
              options: q.options_json ? JSON.parse(q.options_json) : [],
              answer: q.answer,
              explanation: q.explanation
            })),
            fill_in_blank: fillInBlankQuestions.map(q => ({
              id: q.id,
              question: q.stem,
              answer: q.answer,
              explanation: q.explanation
            }))
          }}
          answers={answers}
          score={score ?? 0}
          scoreResult={scoreResult}
        />
      )}
    </div>
  );
};

export default QuizExamView;
