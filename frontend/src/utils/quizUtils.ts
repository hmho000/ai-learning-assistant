const OPTION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

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

