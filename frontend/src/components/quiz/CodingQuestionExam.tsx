import { useState } from "react";
import CodingQuestion from "../CodingQuestion";
import { reviewCode } from "../../api";
import Editor from "@monaco-editor/react";

interface CodingQuestionExamProps {
    index: number;
    question: {
        id: number;
        question: string; // Description
        answer: string; // Initial code template or answer
        explanation?: string;
    };
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
    showAnswer?: boolean;
}

const CodingQuestionExam = ({
    index,
    question,
    value,
    onChange,
    disabled = false,
    showAnswer = false,
}: CodingQuestionExamProps) => {

    const handleReview = async (id: number, code: string) => {
        return await reviewCode(id, code);
    };

    // CodingQuestion component manages its own state for code, but we need to sync it up or pass it down.
    // The CodingQuestion component I created earlier takes `question` and `onReview`.
    // It uses `question.answer` as initial code.
    // Here `value` is the current user code.

    // We need to adapt CodingQuestion to be controlled or just let it be uncontrolled and sync on change?
    // My CodingQuestion implementation:
    // const [code, setCode] = useState(question.answer || "// ...");
    // onChange prop in Editor calls setCode.

    // I should modify CodingQuestion to accept `code` and `onChange` props if I want it controlled by ExamView.
    // But for now, let's just pass the necessary props.
    // Actually, CodingQuestion in my previous step was:
    // const [code, setCode] = useState(question.answer || ...);
    // It didn't accept external code prop.

    // To make it work with ExamView state, I should probably modify CodingQuestion to be controlled.
    // However, since I can't easily modify it again without context switch, I will wrap it here.
    // Wait, I CAN modify it. But let's see if I can just use it as is.
    // If I use it as is, the state in ExamView won't be updated.

    // Let's rewrite CodingQuestion here inline or import a better version?
    // No, I should use the one I created.
    // I will modify CodingQuestion.jsx to accept `value` and `onChange` optionally.

    // Actually, let's just reimplement the wrapper logic here using the Editor directly if needed, 
    // OR, better, modify CodingQuestion.jsx to be more flexible.

    // Let's assume I will modify CodingQuestion.jsx in the next step to be controlled.
    // Or I can just pass `value` and `onChange` to it if I modify it.

    // Let's write this component assuming CodingQuestion accepts `code` and `onChange`.

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-brand-blue mb-2">
                代码题 · 第 {index} 题
            </p>
            <p className="text-base text-slate-800 mb-4 whitespace-pre-line">
                {question.question}
            </p>

            <CodingQuestion
                question={{ ...question, answer: value || question.answer }} // Pass current value as answer (template)
                onReview={handleReview}
                // If I can't control it, I might lose state on re-render if key changes.
                // But let's try to pass a key to force re-init if needed, or better:
                // I will modify CodingQuestion.jsx to accept `value` and `onChange`.
                value={value}
                onChange={onChange}
                readOnly={disabled}
                showReviewButton={showAnswer}
            />

            {showAnswer && (
                <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
                    <p className="font-semibold text-gray-900 mb-2">参考答案：</p>
                    <div className="rounded-lg overflow-hidden border border-slate-200 mb-3">
                        <Editor
                            height="200px"
                            language="python"
                            theme="vs-light"
                            value={question.answer}
                            options={{
                                readOnly: true,
                                minimap: { enabled: false },
                                fontSize: 13,
                                lineNumbers: 'on',
                                scrollBeyondLastLine: false,
                                automaticLayout: true,
                                wordWrap: 'on'
                            }}
                        />
                    </div>
                    {question.explanation && (
                        <>
                            <p className="font-semibold text-gray-900">解析：</p>
                            <p className="mt-1 whitespace-pre-line">{question.explanation}</p>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

export default CodingQuestionExam;
