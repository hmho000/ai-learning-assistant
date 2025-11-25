export interface QuestionStat {
  attempts: number;
  correctAttempts: number;
  lastCorrect: boolean;
  lastAnsweredAt: string;
}

export interface ChapterStats {
  totalAttempts: number;
  totalCorrect: number;
  perQuestion: Record<string, QuestionStat>;
}

const STORAGE_PREFIX = "aiQuizStats";

const isBrowser =
  typeof window !== "undefined" && typeof window.localStorage !== "undefined";

const defaultStats: ChapterStats = {
  totalAttempts: 0,
  totalCorrect: 0,
  perQuestion: {},
};

function cloneStats(stats: ChapterStats): ChapterStats {
  return {
    totalAttempts: stats.totalAttempts,
    totalCorrect: stats.totalCorrect,
    perQuestion: { ...stats.perQuestion },
  };
}

function buildKey(courseId: string, chapterId: number): string {
  return `${STORAGE_PREFIX}:${courseId}:${chapterId}`;
}

function readStats(courseId: string, chapterId: number): ChapterStats {
  if (!isBrowser) {
    return cloneStats(defaultStats);
  }
  const key = buildKey(courseId, chapterId);
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return cloneStats(defaultStats);
  }
  try {
    const parsed = JSON.parse(raw) as ChapterStats;
    if (!parsed || typeof parsed !== "object") {
      return cloneStats(defaultStats);
    }
    return {
      totalAttempts: parsed.totalAttempts || 0,
      totalCorrect: parsed.totalCorrect || 0,
      perQuestion: parsed.perQuestion || {},
    };
  } catch {
    return cloneStats(defaultStats);
  }
}

function writeStats(
  courseId: string,
  chapterId: number,
  stats: ChapterStats
): void {
  if (!isBrowser) {
    return;
  }
  const key = buildKey(courseId, chapterId);
  window.localStorage.setItem(key, JSON.stringify(stats));
}

export function getChapterStats(
  courseId: string,
  chapterId: number
): ChapterStats | null {
  if (!courseId || !chapterId) {
    return null;
  }
  return readStats(courseId, chapterId);
}

export function updateQuestionStat(
  courseId: string,
  chapterId: number,
  questionKey: string,
  isCorrect: boolean
): ChapterStats {
  const stats = readStats(courseId, chapterId);
  stats.totalAttempts += 1;
  if (isCorrect) {
    stats.totalCorrect += 1;
  }

  const questionStat = stats.perQuestion[questionKey] || {
    attempts: 0,
    correctAttempts: 0,
    lastCorrect: false,
    lastAnsweredAt: "",
  };
  questionStat.attempts += 1;
  if (isCorrect) {
    questionStat.correctAttempts += 1;
  }
  questionStat.lastCorrect = isCorrect;
  questionStat.lastAnsweredAt = new Date().toISOString();

  stats.perQuestion[questionKey] = questionStat;
  writeStats(courseId, chapterId, stats);
  return stats;
}

export function getWrongQuestions(
  courseId: string,
  chapterId: number,
  threshold = 0.5
): string[] {
  const stats = readStats(courseId, chapterId);
  const result: string[] = [];
  Object.entries(stats.perQuestion).forEach(([key, value]) => {
    if (!value.attempts) {
      result.push(key);
      return;
    }
    const accuracy = value.correctAttempts / value.attempts;
    if (accuracy < threshold) {
      result.push(key);
    }
  });
  return result;
}

/**
 * 保存答题结果（答题模式使用）
 */
export function saveQuizResult(result: {
  courseId: string;
  chapterId: number;
  score: number;
  total: number;
  timestamp: number;
  answers: Array<{ questionId: string; value: string | string[] }>;
  detail?: Array<{ questionId: string; correct: boolean }>;
}): void {
  if (!isBrowser) {
    return;
  }

  const resultKey = `${STORAGE_PREFIX}:result:${result.courseId}:${result.chapterId}`;
  const results = JSON.parse(
    window.localStorage.getItem(resultKey) || "[]"
  ) as Array<typeof result>;
  results.push(result);
  window.localStorage.setItem(resultKey, JSON.stringify(results));

  // 同时更新统计信息
  const stats = readStats(result.courseId, result.chapterId);
  stats.totalAttempts += 1;
  stats.totalCorrect += result.score;

  // 更新每道题的统计
  if (result.detail) {
    result.detail.forEach((item) => {
      const questionKey = item.questionId;
      const questionStat = stats.perQuestion[questionKey] || {
        attempts: 0,
        correctAttempts: 0,
        lastCorrect: false,
        lastAnsweredAt: "",
      };
      questionStat.attempts += 1;
      if (item.correct) {
        questionStat.correctAttempts += 1;
      }
      questionStat.lastCorrect = item.correct;
      questionStat.lastAnsweredAt = new Date().toISOString();
      stats.perQuestion[questionKey] = questionStat;
    });
  } else {
    // 如果没有 detail，则只更新总统计
    result.answers.forEach((answer) => {
      const questionKey = answer.questionId;
      const questionStat = stats.perQuestion[questionKey] || {
        attempts: 0,
        correctAttempts: 0,
        lastCorrect: false,
        lastAnsweredAt: "",
      };
      questionStat.attempts += 1;
      stats.perQuestion[questionKey] = questionStat;
    });
  }

  writeStats(result.courseId, result.chapterId, stats);
}

