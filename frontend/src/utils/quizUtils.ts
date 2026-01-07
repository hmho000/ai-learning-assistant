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
export function calcScore(quiz: any, answers: UserAnswer[]): ScoreResult {
  const detail: { questionId: string; correct: boolean }[] = [];
  let correctCount = 0;
  let totalCount = 0;

  // Helper to process questions
  const processQuestion = (q: any, typePrefix: string, checkFn: (q: any, ans: any) => boolean) => {
    totalCount++;
    const questionId = `${typePrefix}-${q.id}`;
    const userAnswer = answers.find((a) => a.questionId === questionId);
    let isCorrect = false;

    if (userAnswer) {
      isCorrect = checkFn(q, userAnswer.value);
    }

    if (isCorrect) {
      correctCount++;
    }

    detail.push({
      questionId,
      correct: isCorrect,
    });
  };

  // 1. Multiple Choice
  if (quiz.multiple_choice) {
    quiz.multiple_choice.forEach((q: any) => {
      processQuestion(q, 'mc', (q, val) => {
        const userValue = Array.isArray(val) ? val[0] : val;
        const answerLetter = extractAnswerLetter(q.answer);
        const userLetter = extractAnswerLetter(userValue);
        if (answerLetter && userLetter) {
          return answerLetter === userLetter;
        }
        return normalizeAnswer(userValue) === normalizeAnswer(q.answer);
      });
    });
  }

  // 2. Multi Select
  if (quiz.multi_select) {
    quiz.multi_select.forEach((q: any) => {
      processQuestion(q, 'ms', (q, val) => {
        // val should be array of strings (letters)
        if (!Array.isArray(val) || val.length === 0) return false;

        let correctAnswers: string[] = [];
        try {
          correctAnswers = Array.isArray(q.answer) ? q.answer : JSON.parse(q.answer);
        } catch {
          correctAnswers = [q.answer];
        }

        // Normalize both to sorted letters
        const normUser = val.map(v => extractAnswerLetter(v)).filter(Boolean).sort().join('');
        const normCorrect = correctAnswers.map(v => extractAnswerLetter(v)).filter(Boolean).sort().join('');

        return normUser === normCorrect;
      });
    });
  }

  // 3. True/False
  if (quiz.true_false) {
    quiz.true_false.forEach((q: any) => {
      processQuestion(q, 'tf', (q, val) => {
        return String(val).toLowerCase() === String(q.answer).toLowerCase();
      });
    });
  }

  // 4. Fill in Blank
  if (quiz.fill_in_blank) {
    quiz.fill_in_blank.forEach((q: any) => {
      processQuestion(q, 'fb', (q, val) => {
        const userValue = Array.isArray(val) ? val[0] : val;
        return checkFillBlank(userValue, q.answer);
      });
    });
  }

  // 5. Short Answer (Manual/AI Grading - Counted in total but not auto-correct)
  if (quiz.short_answer) {
    quiz.short_answer.forEach((q: any) => {
      // For now, we mark them as incorrect or pending. 
      // To avoid "0/X" looking bad if they answered, maybe we can check if they answered something?
      // But strictly speaking, score is for *correct* answers.
      // Let's count them in total, but they won't be "correct" automatically.
      processQuestion(q, 'sa', () => false);
    });
  }

  // 6. Coding (Manual/AI Grading)
  if (quiz.coding) {
    quiz.coding.forEach((q: any) => {
      processQuestion(q, 'code', () => false);
    });
  }

  return {
    score: correctCount,
    total: totalCount,
    detail,
  };
}

