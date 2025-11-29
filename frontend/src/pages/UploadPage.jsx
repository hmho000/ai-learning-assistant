import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { uploadFile, generateCourse, parseCourse, fetchChapters, fetchChapterQuiz } from '../api';
export default function UploadPage() {
    const [file, setFile] = useState(null);
    const [step, setStep] = useState('upload'); // upload, processing, complete
    const [logs, setLogs] = useState([]);
    const [courseId, setCourseId] = useState(null);
    const [error, setError] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);
    const navigate = useNavigate();

    const addLog = (msg) => {
        setLogs(prev => [...prev, msg]);
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setError(null);
        }
    };

    const startProcess = async () => {
        if (!file) return;

        setStep('processing');
        setLogs([]);
        setError(null);

        try {
            // 1. Upload
            addLog("正在上传文件...");
            const uploadRes = await uploadFile(file);
            const cid = uploadRes.course_id;
            setCourseId(cid);
            addLog(`上传成功: ${uploadRes.filename}`);

            // 2. Trigger Parsing
            addLog("正在解析章节...");
            await parseCourse(cid);
            addLog("解析任务已提交...");

            // 3. Poll for progress
            let attempts = 0;
            const maxAttempts = 30; // 60 seconds timeout

            const pollInterval = setInterval(async () => {
                attempts++;
                try {
                    const chapters = await fetchChapters(cid);
                    if (chapters.length > 0) {
                        addLog(`已解析 ${chapters.length} 个章节`);
                        clearInterval(pollInterval);
                        addLog("即将跳转到配置页面...");
                        setTimeout(() => {
                            navigate(`/course/${cid}/config`);
                        }, 1000);
                    } else {
                        addLog(`正在解析 PDF... (尝试 ${attempts}/${maxAttempts})`);
                    }

                    if (attempts >= maxAttempts) {
                        clearInterval(pollInterval);
                        setError("生成超时，请稍后在仪表盘查看结果。");
                        setStep('complete'); // Allow user to go back even if timeout
                    }
                } catch (err) {
                    console.error(err);
                }
            }, 2000);

        } catch (err) {
            console.error(err);
            setError("处理过程中发生错误");
            setStep('upload');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center">
            <div className="bg-white w-full max-w-2xl rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">新建课程</h2>

                {step === 'upload' && (
                    <div className="space-y-6">
                        <div
                            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-500 hover:bg-blue-50'
                                }`}
                            onClick={() => fileInputRef.current?.click()}
                            onDragOver={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsDragging(true);
                            }}
                            onDragEnter={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsDragging(true);
                            }}
                            onDragLeave={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsDragging(false);
                            }}
                            onDrop={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsDragging(false);
                                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                                    const droppedFile = e.dataTransfer.files[0];
                                    if (droppedFile.type === "application/pdf") {
                                        setFile(droppedFile);
                                        setError(null);
                                    } else {
                                        setError("请上传 PDF 文件");
                                    }
                                }
                            }}
                        >
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                accept=".pdf"
                                onChange={handleFileChange}
                            />
                            <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Upload size={32} />
                            </div>
                            <p className="text-lg font-medium text-gray-900">点击或拖拽上传 PDF 教材</p>
                            <p className="text-gray-500 mt-2">支持 PDF 格式，最大 200MB</p>
                        </div>

                        {file && (
                            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                                <FileText className="text-blue-600" />
                                <span className="font-medium text-gray-700 flex-1">{file.name}</span>
                                <button
                                    onClick={() => setFile(null)}
                                    className="text-gray-400 hover:text-red-500"
                                >
                                    移除
                                </button>
                            </div>
                        )}

                        {error && (
                            <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="flex gap-4">
                            <button
                                onClick={() => navigate('/')}
                                className="flex-1 py-3 px-6 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
                            >
                                取消
                            </button>
                            <button
                                onClick={startProcess}
                                disabled={!file}
                                className="flex-1 py-3 px-6 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                开始生成
                            </button>
                        </div>
                    </div>
                )}

                {step === 'processing' && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-center py-8">
                            <Loader2 size={48} className="text-blue-600 animate-spin" />
                        </div>
                        <h3 className="text-center text-xl font-medium text-gray-900">AI 正在处理您的教材...</h3>

                        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                            {logs.map((log, i) => (
                                <div key={i} className="mb-1">
                                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> {log}
                                </div>
                            ))}
                            <div className="animate-pulse">_</div>
                        </div>
                    </div>
                )}

                {step === 'complete' && (
                    <div className="text-center py-8">
                        <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                            <CheckCircle size={40} />
                        </div>
                        <h3 className="text-2xl font-bold text-gray-900 mb-2">生成完成！</h3>
                        <p className="text-gray-500 mb-8">您的课程题库已准备就绪。</p>

                        <div className="flex gap-4 justify-center">
                            <button
                                onClick={() => navigate('/')}
                                className="py-3 px-8 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
                            >
                                返回首页
                            </button>
                            <button
                                onClick={() => navigate(`/course/${courseId}`)}
                                className="py-3 px-8 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700"
                            >
                                开始学习
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
