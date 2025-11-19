"""
parse_pdf_demo.py
--------------------

融合版脚本：在章节提取基础上增加文本清洗：
- 自动解析 PDF 路径
- 支持命令行参数
- 支持多处“第X章”标题出现（例如总目录 + 正文）
- 自动选择最长的章节区段作为正文，避免误抓目录页
- 对提取的文本做轻量清洗：去掉页码 / 竖排装饰文字、合并断行
"""

import argparse
import itertools
import re
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF


# -------------------------
# 全局路径配置
# -------------------------
PDF_FILENAME = "数据结构（C语言版）（第3版）双色版 (李冬梅,严蔚敏,吴伟民) (Z-Library).pdf"
PDF_PATH = Path(f"/mnt/data/{PDF_FILENAME}")
DEFAULT_MIN_CHARS = 4000
DEFAULT_MAX_CHARS = 6000
REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PDF_CANDIDATES: List[Path] = [
    PDF_PATH,
    REPO_ROOT / "data" / PDF_FILENAME,
    Path.cwd() / "data" / PDF_FILENAME,
]


# -------------------------
# PDF 路径解析
# -------------------------
def resolve_pdf_path(user_input: Optional[str]) -> Path:
    """根据用户输入或默认候选路径寻找 PDF。"""
    candidates: List[Path] = []
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


# -------------------------
# PDF 解析
# -------------------------
def load_pdf_text(pdf_path: Path) -> str:
    """将整本 PDF 抽成纯文本。"""
    print(f"正在载入 PDF：{pdf_path}")
    doc = fitz.open(pdf_path)

    try:
        pages: List[str] = []
        for page in doc:
            text = page.get_text("text")
            pages.append(text)
        page_count = doc.page_count
    finally:
        doc.close()

    full_text = "\n".join(pages)
    print(f"PDF 载入完成，共 {page_count} 页。")
    return full_text


# -------------------------
# 构造章节匹配正则
# -------------------------
def build_chapter_pattern(chapter_label: str) -> re.Pattern:
    """
    支持：
    - “第2章”
    - “第 2 章”
    - “第二章”
    - “第2章 线性表”
    """
    match = re.search(r"第\s*([0-9一二三四五六七八九十]+)\s*章", chapter_label)
    if match:
        chapter_no_raw = match.group(1)
        cn_map = {
            "一": "1",
            "二": "2",
            "三": "3",
            "四": "4",
            "五": "5",
            "六": "6",
            "七": "7",
            "八": "8",
            "九": "9",
            "十": "10",
        }
        chapter_no = cn_map.get(chapter_no_raw, chapter_no_raw)
        dynamic_pattern = rf"(第\s*{chapter_no}\s*章[^\n]*)"
    else:
        escaped = re.escape(chapter_label)
        dynamic_pattern = rf"({escaped}[^\n]*)"

    print(f"使用章节匹配正则：{dynamic_pattern}")
    return re.compile(dynamic_pattern, re.IGNORECASE)


# -------------------------
# 找出所有“本章到下一章”的区间
# -------------------------
def find_chapter_segments(
    full_text: str, chapter_pattern: re.Pattern
) -> List[Tuple[int, int, str]]:
    """
    返回所有区间：从每次匹配“第X章”开始，到下一次“第Y章”前结束。
    """
    matches = list(chapter_pattern.finditer(full_text))
    if not matches:
        return []

    print(f"找到 {len(matches)} 处章节标题匹配。")

    next_chapter_pattern = re.compile(r"(第\s*\d+\s*章[^\n]*)", re.IGNORECASE)
    segments: List[Tuple[int, int, str]] = []

    for idx, m in enumerate(matches):
        start = m.start()
        next_match = next_chapter_pattern.search(full_text, m.end())
        end = next_match.start() if next_match else len(full_text)
        seg_text = full_text[start:end].strip()

        print(f"- 匹配 #{idx + 1}: 区间 [{start}, {end}), 长度 {len(seg_text)} 字符。")
        segments.append((start, end, seg_text))

    return segments


# -------------------------
# 选取最长（最可能是正文）的区间
# -------------------------
def choose_best_segment(segments: List[Tuple[int, int, str]]) -> Optional[str]:
    if not segments:
        return None
    best = max(segments, key=lambda item: len(item[2]))
    print(f"选择长度最长的区间作为本章正文：{len(best[2])} 字符")
    return best[2]


# -------------------------
# 文本清洗辅助
# -------------------------
def _is_page_number_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.isdigit() and 1 <= len(stripped) <= 3


def _looks_like_code_line(line: str) -> bool:
    stripped = line.rstrip()
    if not stripped:
        return False
    # 缩进行 / 含常见代码符号 / C风格注释
    if stripped[0] in (" ", "\t"):
        return True
    if any(sym in stripped for sym in (";", "{", "}", "->", "==", "!=", "//", "/*", "*/", "#include")):
        return True
    # 粗暴一点：含明显类型/关键字组合
    if re.search(r"\b(void|int|float|double|char|LinkList|SqList)\b", stripped):
        return True
    return False


def clean_extracted_text(text: str) -> str:
    """
    对提取出的章节文本做轻量清洗：
    - 去掉页码
    - 去掉大块竖排装饰文字
    - 合并正文中的断行
    - 压缩多余空行
    """
    # 将全角空格等统一成半角空格
    text = text.replace("\u3000", " ").replace("\xa0", " ")

    lines = text.splitlines()

    cleaned_lines: List[str] = []
    buffer_block: List[str] = []

    def flush_buffer():
        nonlocal buffer_block, cleaned_lines
        if not buffer_block:
            return
        # 判定是否为“竖排装饰块”：大部分行只有 1–2 个字符
        single_char_lines = [ln for ln in buffer_block if len(ln.strip()) <= 2 and ln.strip()]
        if len(buffer_block) >= 5 and len(single_char_lines) / len(buffer_block) > 0.7:
            # 丢弃整个块
            buffer_block = []
            return
        cleaned_lines.extend(buffer_block)
        buffer_block = []

    for ln in lines:
        # 去掉明显是页码的行
        if _is_page_number_line(ln):
            continue
        # 按空行切分 block，用于识别竖排块
        if ln.strip() == "":
            flush_buffer()
            cleaned_lines.append("")
        else:
            buffer_block.append(ln)

    flush_buffer()

    # 合并断行：对“非代码行”的中文/说明文字进行合并
    merged_lines: List[str] = []
    prev_was_text = False

    for ln in cleaned_lines:
        if ln.strip() == "":
            merged_lines.append("")
            prev_was_text = False
            continue

        if _looks_like_code_line(ln):
            # 代码行：原样保留
            merged_lines.append(ln.rstrip())
            prev_was_text = False
            continue

        # 普通说明/正文行：尝试和上一行合并
        current = ln.strip()
        if not merged_lines:
            merged_lines.append(current)
            prev_was_text = True
            continue

        prev = merged_lines[-1]

        if prev_was_text:
            # 如果上一行不是以句号/问号/感叹号/冒号/分号/大括号等结尾，就认为是同一段
            if not re.search(r"[。！？；:.!?】】）\}\]]$", prev):
                merged_lines[-1] = prev + " " + current
            else:
                merged_lines.append(current)
        else:
            merged_lines.append(current)

        prev_was_text = True

    # 压缩多余空行：连续空行只保留一个
    final_lines: List[str] = []
    for key, group in itertools.groupby(merged_lines):
        if key == "":
            final_lines.append("")
        else:
            final_lines.extend(list(group))

    return "\n".join(final_lines).strip()


# -------------------------
# 提取章节文本（融合 + 清洗）
# -------------------------
def extract_chapter(
    full_text: str,
    chapter_pattern: re.Pattern,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> Optional[str]:
    segments = find_chapter_segments(full_text, chapter_pattern)
    if not segments:
        return None

    chapter_text = choose_best_segment(segments)
    if not chapter_text:
        return None

    clipped = chapter_text[:max_chars]
    if len(clipped) < min_chars and len(chapter_text) > min_chars:
        clipped = chapter_text[:min_chars]

    print(
        f"原始提取文本长度：{len(chapter_text)} 字符，"
        f"截取后：{len(clipped)} 字符。"
    )

    cleaned = clean_extracted_text(clipped)
    print(f"清洗后文本长度：{len(cleaned)} 字符。")
    return cleaned


# -------------------------
# 保存输出
# -------------------------
def save_output(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"输出已保存到：{output_path}")


# -------------------------
# 主函数
# -------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="解析 PDF 指定章节并输出清洗后的文本"
    )
    parser.add_argument(
        "--chapter",
        required=True,
        help="目标章节，例如：第2章 / 第 2 章 / 第二章",
    )
    parser.add_argument(
        "--output",
        default="experiments/output/chapter_2.txt",
        help="输出文件路径",
    )
    parser.add_argument(
        "--pdf",
        default=str(PDF_PATH),
        help="PDF 文件路径",
    )
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
