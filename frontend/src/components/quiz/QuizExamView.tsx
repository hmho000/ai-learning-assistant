import React, { useState, useMemo } from "react";
import { UserAnswer } from "../../types/quiz";
import MultipleChoiceQuestionExam from "./MultipleChoiceQuestionExam";
import MultiSelectQuestionExam from "./MultiSelectQuestionExam";
import TrueFalseQuestionExam from "./TrueFalseQuestionExam";
import FillInBlankQuestionExam from "./FillInBlankQuestionExam";
import ShortAnswerQuestionExam from "./ShortAnswerQuestionExam";
import CodingQuestionExam from "./CodingQuestionExam";
import QuizExamSummary from "./QuizExamSummary";
import { saveQuizResult } from "../../utils/quizStorage";
import { calcScore } from "../../utils/quizUtils";
import { mistakeApi, gradeShortAnswer, reviewCode } from "../../api";

// 如果未导入，则定义 API 数据结构的本地接口
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

  // 按类型筛选题目
  const multipleChoiceQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "multiple_choice"),
    [quiz.questions]);

  const multiSelectQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "multi_select"),
    [quiz.questions]);

  const trueFalseQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "true_false"),
    [quiz.questions]);

  const fillInBlankQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "fill_in_blank"),
    [quiz.questions]);

  const shortAnswerQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "short_answer"),
    [quiz.questions]);

  const codingQuestions = useMemo(() =>
    quiz.questions.filter(q => q.type === "coding"),
    [quiz.questions]);

  const handleAnswerChange = (questionId: string, value: any) => {
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

  const [isGrading, setIsGrading] = useState(false);

  const handleSubmit = async () => {
    setIsGrading(true);

    const quizFormat = {
      meta: {
        chapter_index: 0,
        chapter_title: "Chapter",
        quiz_title: quiz.title,
        quiz_description: "Generated Quiz"
      },
      multiple_choice: multipleChoiceQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        options: q.options_json ? JSON.parse(q.options_json) : [],
        answer: q.answer,
        explanation: q.explanation || ""
      })),
      multi_select: multiSelectQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        options: q.options_json ? JSON.parse(q.options_json) : [],
        answer: q.answer,
        explanation: q.explanation || ""
      })),
      true_false: trueFalseQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        answer: q.answer,
        explanation: q.explanation || ""
      })),
      fill_in_blank: fillInBlankQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        answer: q.answer,
        explanation: q.explanation || ""
      })),
      short_answer: shortAnswerQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        answer: q.answer,
        explanation: q.explanation || ""
      })),
      coding: codingQuestions.map(q => ({
        id: q.id,
        question: q.stem,
        answer: q.answer,
        explanation: q.explanation || ""
      }))
    };

    // 1. 计算客观题得分
    const result = calcScore(quizFormat, answers);

    // 2. 简答题和代码题的 AI 评分
    // 仅当有题目且用户已作答时进行
    const gradingPromises: Promise<void>[] = [];

    // 简答题评分
    shortAnswerQuestions.forEach(q => {
      const ans = answers.find(a => a.questionId === `sa-${q.id}`);
      if (ans && ans.value && String(ans.value).trim()) {
        gradingPromises.push(
          gradeShortAnswer(q.id, String(ans.value)).then(res => {
            // 如果得分 >= 6，算作正确
            if (res.score >= 6) {
              result.score++;
              const detailItem = result.detail.find(d => d.questionId === `sa-${q.id}`);
              if (detailItem) detailItem.correct = true;
            }
          }).catch(err => console.error("简答题评分错误", err))
        );
      }
    });

    // 代码题评分
    codingQuestions.forEach(q => {
      const ans = answers.find(a => a.questionId === `code-${q.id}`);
      if (ans && ans.value && String(ans.value).trim()) {
        gradingPromises.push(
          reviewCode(q.id, String(ans.value)).then(res => {
            // 如果得分 >= 6，算作正确
            if (res.score >= 6) {
              result.score++;
              const detailItem = result.detail.find(d => d.questionId === `code-${q.id}`);
              if (detailItem) detailItem.correct = true;
            }
          }).catch(err => console.error("代码题评分错误", err))
        );
      }
    });

    if (gradingPromises.length > 0) {
      await Promise.all(gradingPromises); // 等待所有 AI 评分完成
    }

    setScore(result.score);
    setScoreResult(result);
    setSubmitted(true);
    setIsGrading(false);

    saveQuizResult({
      courseId: courseId ? String(courseId) : "default-course",
      chapterId,
      score: result.score,
      total: result.total,
      timestamp: Date.now(),
      answers,
      detail: result.detail,
    });

    // 将错题添加到错题本
    if (courseId) {
      const wrongQuestions = result.detail.filter((d) => !d.correct);
      wrongQuestions.forEach((detail) => {
        // 从 questionId 中提取题目 ID（格式：mc-123, fb-123, tf-123 等）
        const questionIdMatch = detail.questionId.match(/^[a-z]+-(\d+)$/i);
        if (questionIdMatch) {
          const questionId = parseInt(questionIdMatch[1]);
          mistakeApi.addMistake(courseId, questionId).catch((error) => {
            console.error("添加错题失败:", error);
          });
        }
      });
    }
  };

  // Helper for dynamic section numbering
  let sectionIndex = 0;
  const getSectionTitle = (title: string) => {
    sectionIndex++;
    const chineseNumbers = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"];
    return `${chineseNumbers[sectionIndex - 1]}、${title}`;
  };

  return (
    <div className="space-y-6">
      {multipleChoiceQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">{getSectionTitle("单选题")}</h2>
          {multipleChoiceQuestions.map((q, index) => {
            const options = q.options_json ? JSON.parse(q.options_json) : [];
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

      {multiSelectQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">{getSectionTitle("多选题")}</h2>
          {multiSelectQuestions.map((q, index) => {
            const options = q.options_json ? JSON.parse(q.options_json) : [];
            const qProps = {
              id: q.id,
              question: q.stem,
              options: options,
              answer: q.answer, // String or JSON string
              explanation: q.explanation
            };

            return (
              <MultiSelectQuestionExam
                key={q.id}
                index={index + 1}
                question={qProps}
                value={(answers.find((a) => a.questionId === `ms-${q.id}`)?.value as string[]) ?? []}
                onChange={(value) => handleAnswerChange(`ms-${q.id}`, value)}
                disabled={submitted}
                showAnswer={submitted}
              />
            );
          })}
        </section>
      )}

      {trueFalseQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">{getSectionTitle("判断题")}</h2>
          {trueFalseQuestions.map((q, index) => {
            const qProps = {
              id: q.id,
              question: q.stem,
              options: ["True", "False"],
              answer: q.answer,
              explanation: q.explanation
            };

            return (
              <TrueFalseQuestionExam
                key={q.id}
                index={index + 1}
                question={qProps}
                value={(answers.find((a) => a.questionId === `tf-${q.id}`)?.value as string) ?? ""}
                onChange={(value) => handleAnswerChange(`tf-${q.id}`, value)}
                disabled={submitted}
                showAnswer={submitted}
              />
            );
          })}
        </section>
      )}

      {fillInBlankQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">{getSectionTitle("填空题")}</h2>
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

      {shortAnswerQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">{getSectionTitle("简答题")}</h2>
          {shortAnswerQuestions.map((q, index) => {
            const qProps = {
              id: q.id,
              question: q.stem,
              answer: q.answer,
              explanation: q.explanation
            };

            return (
              <ShortAnswerQuestionExam
                key={q.id}
                index={index + 1}
                question={qProps}
                value={
                  (answers.find((a) => a.questionId === `sa-${q.id}`)?.value as string) ?? ""
                }
                onChange={(value) => handleAnswerChange(`sa-${q.id}`, value)}
                disabled={submitted}
                showAnswer={submitted}
              />
            );
          })}
        </section>
      )}

      {codingQuestions.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-2">{getSectionTitle("代码题")}</h2>
          {codingQuestions.map((q, index) => {
            const qProps = {
              id: q.id,
              question: q.stem,
              answer: q.answer, // Template
              explanation: q.explanation
            };

            return (
              <CodingQuestionExam
                key={q.id}
                index={index + 1}
                question={qProps}
                value={
                  (answers.find((a) => a.questionId === `code-${q.id}`)?.value as string) ?? ""
                }
                onChange={(value) => handleAnswerChange(`code-${q.id}`, value)}
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
            className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600 transition disabled:opacity-50 flex items-center gap-2"
            onClick={handleSubmit}
            disabled={isGrading}
          >
            {isGrading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                AI 评分中...
              </>
            ) : (
              "提交答案"
            )}
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
            meta: {
              chapter_index: 0,
              chapter_title: "Chapter",
              quiz_title: quiz.title,
              quiz_description: "Generated Quiz"
            },
            multiple_choice: multipleChoiceQuestions.map(q => ({
              id: q.id,
              question: q.stem,
              options: q.options_json ? JSON.parse(q.options_json) : [],
              answer: q.answer,
              explanation: q.explanation || ""
            })),
            fill_in_blank: fillInBlankQuestions.map(q => ({
              id: q.id,
              question: q.stem,
              answer: q.answer,
              explanation: q.explanation || ""
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
