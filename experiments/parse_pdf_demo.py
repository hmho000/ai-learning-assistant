"""
parse_pdf_demo.py
-----------------

使用 PyMuPDF 解析《数据结构（C语言版）（第3版）双色版》PDF，
按章节粗略切分并输出指定章节的前若干文字。
"""

import argparse
import re
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF


PDF_FILENAME = "数据结构（C语言版）（第3版）双色版 (李冬梅,严蔚敏,吴伟民) (Z-Library).pdf"
PDF_PATH = Path(f"/mnt/data/{PDF_FILENAME}")
DEFAULT_MIN_CHARS = 3000
DEFAULT_MAX_CHARS = 6000
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_CANDIDATES: List[Path] = [
    PDF_PATH,
    REPO_ROOT / "data" / PDF_FILENAME,
    Path.cwd() / "data" / PDF_FILENAME,
]


def resolve_pdf_path(user_input: Optional[str]) -> Path:
    """根据用户输入或默认候选路径寻找 PDF。"""
    candidates = []
    if user_input:
        candidates.append(Path(user_input).expanduser())
    candidates.extend(DEFAULT_PDF_CANDIDATES)

    checked = []
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.exists():
            print(f"使用 PDF 文件：{candidate}")
            return candidate
        checked.append(str(candidate))

    details = "\n - ".join(checked)
    raise FileNotFoundError(
        "未找到 PDF 文件，请使用 --pdf 指定实际路径。已检查：\n - " + details
    )


def load_pdf_text(pdf_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在：{pdf_path}")

    print(f"正在载入 PDF：{pdf_path}")
    doc = fitz.open(pdf_path)
    try:
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        page_count = doc.page_count
    finally:
        doc.close()

    full_text = "\n".join(pages)
    print(f"PDF 载入完成，共 {page_count} 页。")
    return full_text


def build_chapter_pattern(chapter_label: str) -> re.Pattern:
    """根据章节名称构造正则。"""
    # 示例正则（要求中指定）
    pattern = r"第\s*2\s*章.*"
    # 根据参数动态构造
    match = re.match(r"第\s*(\d+)\s*章", chapter_label)
    if match:
        chapter_no = match.group(1)
        dynamic_pattern = rf"(第\s*{chapter_no}\s*章[^\n]*)"
    else:
        escaped = re.escape(chapter_label)
        dynamic_pattern = rf"({escaped}[^\n]*)"

    print(f"使用章节匹配正则：{dynamic_pattern}")
    return re.compile(dynamic_pattern, re.IGNORECASE)


def extract_chapter(
    full_text: str,
    chapter_pattern: re.Pattern,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> Optional[str]:
    """提取指定章节的正文片段。"""
    matches = list(chapter_pattern.finditer(full_text))
    if not matches:
        return None

    start = matches[0].start()

    # 查找下一章的起点
    next_chapter_pattern = re.compile(r"(第\s*\d+\s*章[^\n]*)", re.IGNORECASE)
    next_match = next_chapter_pattern.search(full_text, matches[0].end())
    end = next_match.start() if next_match else len(full_text)

    chapter_text = full_text[start:end].strip()
    clipped = chapter_text[:max_chars]

    if len(clipped) < min_chars and len(chapter_text) > min_chars:
        clipped = chapter_text[:min_chars]

    print(
        f"章节文本长度：{len(chapter_text)} 字符，"
        f"截取后长度：{len(clipped)} 字符。"
    )
    return clipped


def save_output(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"输出已保存到：{output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="解析 PDF 指定章节")
    parser.add_argument("--chapter", required=True, help="目标章节，例如：第2章")
    parser.add_argument(
        "--output",
        default="experiments/output/chapter_2.txt",
        help="输出文件路径",
    )
    parser.add_argument("--pdf", default=str(PDF_PATH), help="PDF 文件路径")
    parser.add_argument(
        "--min-chars",
        type=int,
        default=DEFAULT_MIN_CHARS,
        help="输出文本最小字符数",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help="输出文本最大字符数",
    )

    args = parser.parse_args()

    pdf_path = resolve_pdf_path(args.pdf)
    output_path = Path(args.output)
    print(f"正在解析章节：{args.chapter}")

    full_text = load_pdf_text(pdf_path)
    pattern = build_chapter_pattern(args.chapter)
    chapter_text = extract_chapter(
        full_text,
        pattern,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
    )

    if not chapter_text:
        print(f"未找到章节：{args.chapter}")
        return

    save_output(chapter_text, output_path)


if __name__ == "__main__":
    main()

