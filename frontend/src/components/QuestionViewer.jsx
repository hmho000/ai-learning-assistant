import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const QuestionViewer = ({ markdownText = "", heading = "" }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (containerRef.current) {
      containerRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [markdownText, heading]);

  return (
    <section
      ref={containerRef}
      className="markdown-body bg-white rounded-2xl shadow-subtle p-8 md:p-10 mx-auto max-w-3xl"
    >
      {heading && (
        <div className="mb-6 text-sm font-semibold text-slate-500 tracking-wide uppercase">
          {heading}
        </div>
      )}
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownText}</ReactMarkdown>
    </section>
  );
};

export default QuestionViewer;

