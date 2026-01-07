import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mistakeApi } from '../api'; // 导入刚才写的 API

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

  const handleRemove = async (questionId) => {
    if(!confirm("确定要移除这道题吗？")) return;
    await mistakeApi.removeMistake(questionId);
    // 移除后刷新列表
    loadMistakes();
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">📖 智能错题本</h1>
        <button onClick={() => navigate(-1)} className="text-blue-500">返回</button>
      </div>

      {loading ? (
        <div>加载中...</div>
      ) : questions.length === 0 ? (
        <div className="text-center py-20 text-gray-500 bg-white rounded-lg shadow">
          <p>太棒了！目前没有错题 🎉</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {questions.map((q, index) => (
            <div key={q.id} className="bg-white p-6 rounded-lg shadow-md border-l-4 border-red-400 relative">
              {/* 错题标记 */}
              <div className="absolute top-4 right-4 text-xs text-gray-400">
                收录于: {new Date(q.mistake_date).toLocaleDateString()}
              </div>
              
              <h3 className="font-bold text-lg mb-2">
                {q.type === 'multiple_choice' ? '选择题' : '填空题'} 第 {index + 1} 题
              </h3>
              <p className="mb-4 text-gray-800">{q.stem}</p>
              
              {/* 如果是选择题，显示选项 */}
              {q.type === 'multiple_choice' && q.options_json && (
                <div className="mb-4 space-y-2">
                  {JSON.parse(q.options_json).map((option, optIdx) => {
                    const optionLabel = String.fromCharCode(65 + optIdx); // A, B, C, D...
                    const isCorrect = optionLabel === q.answer || String(optIdx) === q.answer;
                    return (
                      <div
                        key={optIdx}
                        className={`p-2 rounded text-sm ${
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
              
              {/* 答案和解析 */}
              <div className="bg-gray-50 p-3 rounded text-sm text-gray-600 mb-4">
                <span className="font-bold text-green-600">正确答案: {q.answer}</span>
                {q.explanation && <p className="mt-1">解析: {q.explanation}</p>}
              </div>

              <div className="flex justify-end space-x-3">
                 <button 
                   onClick={() => handleRemove(q.id)}
                   className="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 text-sm transition"
                 >
                   ✅ 我学会了 (移除)
                 </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MistakeBookPage;