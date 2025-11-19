import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const QuestionViewer = ({ markdownText = "" }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (containerRef.current) {
      containerRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [markdownText]);

  return (
    <section
      ref={containerRef}
      className="markdown-body bg-white rounded-2xl shadow-subtle p-8 md:p-10 mx-auto max-w-3xl"
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownText}</ReactMarkdown>
    </section>
  );
};

export default QuestionViewer;

