export interface QuizMeta {
  chapter_index: number;
  chapter_title: string;
  quiz_title: string;
  quiz_description: string;
}

export interface MultipleChoiceQuestion {
  id: number;
  question: string;
  options: string[];
  answer: string;
  explanation: string;
}

export interface FillInBlankQuestion {
  id: number;
  question: string;
  answer: string | string[];
  explanation: string;
}

export interface QuizData {
  meta: QuizMeta;
  multiple_choice: MultipleChoiceQuestion[];
  fill_in_blank: FillInBlankQuestion[];
}

export interface ChapterManifest {
  id: number;
  sourceTitle: string;
  quizTitle: string;
  file: string;
  jsonFile?: string;
  description?: string;
}

export interface CourseManifest {
  id: string;
  name: string;
  sourceFile?: string;
  chapters: ChapterManifest[];
}

