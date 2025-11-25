import type { QuizData, UserAnswer, ScoreResult } from "../types/quiz";

const OPTION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

/**
 * 根据章节号加载 JSON 题库
 */
export async function loadQuizJsonByChapter(chapterId: number): Promise<QuizData> {
  const res = await fetch(`/questions/ch${chapterId}_questions.json`);
  if (!res.ok) {
    throw new Error(`加载题库失败: ch${chapterId}_questions.json`);
  }
  return res.json();
}

export function normalizeAnswer(value: string): string {
  return (value || "")
    .trim()
    .replace(/\s+/g, "")
    .toLowerCase();
}

export function checkFillBlank(
  userInput: string,
  correct: string | string[]
): boolean {
  const answers = Array.isArray(correct) ? correct : [correct];
  const normalizedUser = normalizeAnswer(userInput);
  return answers.some((ans) => normalizeAnswer(ans) === normalizedUser);
}

export function extractOptionLetter(option: string, index: number): string {
  const trimmed = (option || "").trim();
  const match = trimmed.match(/^([A-Z])[\.\)]/i);
  if (match) {
    return match[1].toUpperCase();
  }
  return OPTION_LETTERS[index] || String(index + 1);
}

export function extractAnswerLetter(answer: string): string | null {
  const trimmed = (answer || "").trim();
  if (!trimmed) {
    return null;
  }
  const single = trimmed.match(/^[A-Z]$/i);
  if (single) {
    return single[0].toUpperCase();
  }
  const prefixed = trimmed.match(/^([A-Z])[\.\)]?/i);
  if (prefixed) {
    return prefixed[1].toUpperCase();
  }
  return null;
}

export function isChoiceCorrect(
  option: string,
  optionIndex: number,
  answer: string
): boolean {
  const answerLetter = extractAnswerLetter(answer);
  const optionLetter = extractOptionLetter(option, optionIndex);
  if (answerLetter) {
    return optionLetter === answerLetter;
  }
  return normalizeAnswer(option) === normalizeAnswer(answer);
}

export function formatAnswerDisplay(answer: string | string[]): string {
  if (Array.isArray(answer)) {
    return answer.join(" / ");
  }
  return answer || "";
}

/**
 * 计算答题得分
 */
export function calcScore(quiz: QuizData, answers: UserAnswer[]): ScoreResult {
  const detail: { questionId: string; correct: boolean }[] = [];
  let correctCount = 0;
  let totalCount = 0;

  // 检查选择题
  if (quiz.multiple_choice) {
    quiz.multiple_choice.forEach((q) => {
      totalCount++;
      const userAnswer = answers.find((a) => a.questionId === `mc-${q.id}`);
      let isCorrect = false;

      if (userAnswer) {
        const userValue = Array.isArray(userAnswer.value)
          ? userAnswer.value[0]
          : userAnswer.value;
        const answerLetter = extractAnswerLetter(q.answer);
        const userLetter = extractAnswerLetter(userValue);

        if (answerLetter && userLetter) {
          isCorrect = answerLetter === userLetter;
        } else {
          // 如果没有字母，则进行文本比较
          isCorrect = normalizeAnswer(userValue) === normalizeAnswer(q.answer);
        }
      }

      if (isCorrect) {
        correctCount++;
      }

      detail.push({
        questionId: `mc-${q.id}`,
        correct: isCorrect,
      });
    });
  }

  // 检查填空题
  if (quiz.fill_in_blank) {
    quiz.fill_in_blank.forEach((q) => {
      totalCount++;
      const userAnswer = answers.find((a) => a.questionId === `fb-${q.id}`);
      let isCorrect = false;

      if (userAnswer) {
        const userValue = Array.isArray(userAnswer.value)
          ? userAnswer.value[0]
          : userAnswer.value;
        isCorrect = checkFillBlank(userValue, q.answer);
      }

      if (isCorrect) {
        correctCount++;
      }

      detail.push({
        questionId: `fb-${q.id}`,
        correct: isCorrect,
      });
    });
  }

  return {
    score: correctCount,
    total: totalCount,
    detail,
  };
}

