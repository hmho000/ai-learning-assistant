import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mistakeApi } from '../api';

// 题型中文名称映射
const QUESTION_TYPE_NAMES = {
  'multiple_choice': '单选题',
  'multi_select': '多选题',
  'fill_in_blank': '填空题',
  'true_false': '判断题',
  'short_answer': '简答题',
  'code': '代码题',
};

// 题型排序映射
const QUESTION_TYPE_ORDER = {
  'multiple_choice': 1,
  'multi_select': 2,
  'fill_in_blank': 3,
  'true_false': 4,
  'short_answer': 5,
  'code': 6,
};

const MistakeBookPage = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMistakes();
  }, [courseId]);

  const loadMistakes = async () => {
    if (!courseId) return;
    try {
      const data = await mistakeApi.getMistakes(parseInt(courseId));
      setQuestions(data);
    } catch (error) {
      console.error("加载错题失败", error);
    } finally {
      setLoading(false);
    }
  };

  // 按题型分组
  const groupedQuestions = useMemo(() => {
    const grouped = {};
    questions.forEach(q => {
      const type = q.type || 'unknown';
      if (!grouped[type]) {
        grouped[type] = [];
      }
      grouped[type].push(q);
    });
    return grouped;
  }, [questions]);

  // 获取排序后的题型列表
  const sortedTypes = useMemo(() => {
    return Object.keys(groupedQuestions).sort((a, b) => {
      const orderA = QUESTION_TYPE_ORDER[a] || 999;
      const orderB = QUESTION_TYPE_ORDER[b] || 999;
      return orderA - orderB;
    });
  }, [groupedQuestions]);

  const handleRemove = async (questionId) => {
    if (!confirm("确定要移除这道题吗？")) return;
    try {
      await mistakeApi.removeMistake(parseInt(courseId), questionId);
      loadMistakes();
    } catch (error) {
      console.error("移除错题失败:", error);
      alert("移除失败，请重试");
    }
  };

  // 渲染题目组件
  const renderQuestion = (q, index) => {
    const isMultipleChoice = q.type === 'multiple_choice' || q.type === 'multi_select';
    const isFillingBlank = q.type === 'fill_in_blank';
    const isJudgment = q.type === 'true_false';
    const isShortAnswer = q.type === 'short_answer';
    const isCode = q.type === 'code';

    return (
      <div key={q.id} className="bg-white p-6 rounded-lg shadow-md border-l-4 border-red-400 relative">
        {/* 错题标记 */}
        <div className="absolute top-4 right-4 text-xs text-gray-400">
          收录于: {new Date(q.mistake_date).toLocaleDateString()}
        </div>

        {/* 题型和相对题号（每个quiz内重新计数） */}
        <h3 className="font-bold text-lg mb-2 text-slate-900">
          {QUESTION_TYPE_NAMES[q.type] || q.type} 第 {q.question_number || q.id} 题
        </h3>

        {/* 题干 */}
        <p className="mb-4 text-gray-800 whitespace-pre-wrap">{q.stem}</p>

        {/* 选择题和多选题：显示选项 */}
        {isMultipleChoice && q.options_json && (
          <div className="mb-4 space-y-2">
            {JSON.parse(q.options_json).map((option, optIdx) => {
              const optionLabel = String.fromCharCode(65 + optIdx); // A, B, C, D...
              const isCorrect = optionLabel === q.answer || String(optIdx) === q.answer;
              return (
                <div
                  key={optIdx}
                  className={`p-3 rounded text-sm ${
                    isCorrect
                      ? 'bg-green-50 border border-green-200 text-green-800'
                      : 'bg-gray-50 border border-gray-200 text-gray-700'
                  }`}
                >
                  <span className="font-semibold">{optionLabel}.</span> {option}
                  {isCorrect && <span className="ml-2 text-green-600">✓</span>}
                </div>
              );
            })}
          </div>
        )}

        {/* 判断题：显示答案 */}
        {isJudgment && (
          <div className="mb-4 p-3 rounded bg-blue-50 border border-blue-200">
            <span className="text-sm font-semibold text-blue-800">
              答案：{q.answer === 'true' || q.answer === '正确' || q.answer === 'T' ? '正确' : '错误'}
            </span>
          </div>
        )}

        {/* 填空题、简答题、代码题：直接显示答案 */}
        {(isFillingBlank || isShortAnswer || isCode) && (
          <div className="mb-4 p-3 rounded bg-blue-50 border border-blue-200">
            <span className="text-sm font-semibold text-blue-800">标准答案：</span>
            <p className="text-sm text-blue-700 mt-1 whitespace-pre-wrap">{q.answer}</p>
          </div>
        )}

        {/* 答案和解析区域 */}
        <div className="bg-gray-50 p-3 rounded text-sm text-gray-600 mb-4">
          {!isJudgment && !isFillingBlank && !isShortAnswer && !isCode && (
            <span className="font-bold text-green-600">正确答案: {q.answer}</span>
          )}
          {q.explanation && (
            <p className="mt-2 whitespace-pre-wrap text-gray-700">
              <span className="font-semibold">解析：</span>{q.explanation}
            </p>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={() => handleRemove(q.id)}
            className="px-4 py-2 bg-green-100 text-green-700 rounded hover:bg-green-200 text-sm font-medium transition"
          >
            ✅ 我学会了 (移除)
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">📖 智能错题本</h1>
        <button onClick={() => navigate(-1)} className="px-4 py-2 text-blue-500 hover:bg-blue-50 rounded transition">
          返回
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      ) : questions.length === 0 ? (
        <div className="text-center py-20 text-gray-500 bg-white rounded-lg shadow">
          <p className="text-xl">太棒了！目前没有错题 🎉</p>
        </div>
      ) : (
        <div className="space-y-8">
          {sortedTypes.map((type) => (
            <div key={type}>
              {/* 题型分类标题 */}
              <h2 className="text-xl font-bold text-slate-800 mb-4 pb-2 border-b-2 border-blue-500">
                {QUESTION_TYPE_NAMES[type] || type}
                <span className="ml-2 text-sm text-gray-600 font-normal">
                  ({groupedQuestions[type].length} 题)
                </span>
              </h2>

              {/* 该题型下的所有题目 */}
              <div className="space-y-4">
                {groupedQuestions[type].map((q) =>
                  renderQuestion(q)
                )}
              </div>
            </div>
          ))}

          {/* 统计信息 */}
          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">总计：</span>
              {questions.length} 题
              {sortedTypes.map(type => (
                <span key={type} className="ml-4">
                  | {QUESTION_TYPE_NAMES[type]}: {groupedQuestions[type].length}
                </span>
              ))}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MistakeBookPage;