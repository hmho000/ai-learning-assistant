import axios from 'axios';

// 在开发环境下，Vite 会代理 /api 到后端
// 在生产环境下，前端和后端同源
const api = axios.create({
  baseURL: '/api',
});

export interface Course {
  id: number;
  title: string;
  description: string;
  status: string;
  created_at: string;
}

export interface Chapter {
  id: number;
  course_id: number;
  title: string;
  index: number;
}

export interface Question {
  id: number;
  type: string;
  stem: string;
  options_json?: string;
  answer: string;
  explanation?: string;
}

export interface Quiz {
  id: number;
  chapter_id: number;
  title: string;
  description: string;
  questions: Question[];
}

export const fetchCourses = async () => {
  const res = await api.get<Course[]>('/courses');
  return res.data;
};

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post<{ course_id: number; filename: string }>('/upload', formData);
  return res.data;
};

export const generateCourse = async (courseId: number) => {
  const res = await api.post<{ status: string; message: string }>(`/generate/${courseId}`);
  return res.data;
};

export const parseCourse = async (courseId: number) => {
  const res = await api.post<{ status: string }>(`/courses/${courseId}/parse`);
  return res.data;
};

export const generateCourseCustom = async (courseId: number, config: { chapter_ids: number[], num_mc: number, num_fb: number }) => {
  const res = await api.post<{ status: string }>(`/courses/${courseId}/generate`, config);
  return res.data;
};

export const fetchChapters = async (courseId: number) => {
  const res = await api.get<Chapter[]>(`/courses/${courseId}/chapters`);
  return res.data;
};

export const fetchChapterQuiz = async (chapterId: number) => {
  const res = await api.get<Quiz[]>(`/chapters/${chapterId}/quiz`);
  return res.data;
};

export const deleteCourse = async (courseId: number) => {
  const res = await api.delete<{ status: string; message: string }>(`/courses/${courseId}`);
  return res.data;
};

export const exportChapterQuiz = async (chapterId: number, includeAnswers: boolean) => {
  const res = await api.get(`/chapters/${chapterId}/export-word`, {
    params: { include_answers: includeAnswers },
    responseType: 'blob',
  });
  return res; // Return full response to access headers if needed, or just data
};


// ==================== 错题本 API ====================
// 题型显示顺序和中文名称映射
const QUESTION_TYPE_NAMES: Record<string, string> = {
  'multiple_choice': '单选题',
  'multi_select': '多选题',
  'fill_in_blank': '填空题',
  'true_false': '判断题',
  'short_answer': '简答题',
  'code': '代码题',
};

export const mistakeApi = {
  // 添加错题
  addMistake: async (courseId: number, questionId: number) => {
    const res = await api.post('/mistakes', { 
      course_id: courseId, 
      question_id: questionId 
    });
    return res.data;
  },

  // 获取课程错题（已在后端按题型排序）
  getMistakes: async (courseId: number) => {
    const res = await api.get(`/courses/${courseId}/mistakes`);
    return res.data;
  },

  // 移除错题（修复：现在需要传递 courseId）
  removeMistake: async (courseId: number, questionId: number) => {
    const res = await api.delete(`/courses/${courseId}/mistakes/${questionId}`);
    return res.data;
  },

  // 获取题型中文名称
  getTypeName: (type: string): string => {
    return QUESTION_TYPE_NAMES[type] || type;
  }
};