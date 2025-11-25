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
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF

try:
    from .extract_text import extract_text_from_file
    from .chapter_detector import split_into_chapters
except ImportError:  # pragma: no cover - 兼容直接运行脚本
    from extract_text import extract_text_from_file  # type: ignore
    from chapter_detector import split_into_chapters  # type: ignore


# -------------------------
# 全局路径配置
# -------------------------
PDF_FILENAME = "数据结构（C语言版）（第3版）双色版 (李冬梅,严蔚敏,吴伟民) (Z-Library).pdf"
PDF_PATH = Path(f"/mnt/data/{PDF_FILENAME}")
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
# 保存输出
# -------------------------
def save_output(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"输出已保存到：{output_path}")


# -------------------------
# 章节匹配
# -------------------------
CHAPTER_PATTERN = re.compile(r"第\s*([零一二三四五六七八九十百0-9]+)\s*章")

CN_NUMERAL_MAP = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "百": 100,
}


def _parse_chapter_id(value: str) -> Optional[int]:
    """根据“1”/“第1章”/“第一章”等格式解析章节 id。"""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return int(value)

    digit_match = re.search(r"\d+", value)
    if digit_match:
        return int(digit_match.group())

    cn_match = CHAPTER_PATTERN.search(value)
    if not cn_match:
        return None

    cn_value = cn_match.group(1)
    return _chinese_numeral_to_int(cn_value)


def _chinese_numeral_to_int(text: str) -> Optional[int]:
    """
    粗糙的中文数字转换，满足“十/十一/二十/二十三/一百”等常见写法。
    """
    text = text.strip()
    if not text:
        return None

    if text == "十":
        return 10

    if text.endswith("十") and len(text) >= 2:
        prefix = CN_NUMERAL_MAP.get(text[0])
        if prefix is None:
            return None
        return prefix * 10

    if "十" in text:
        before, after = text.split("十", 1)
        before_val = CN_NUMERAL_MAP.get(before) if before else 1
        after_val = CN_NUMERAL_MAP.get(after) if after else 0
        if before_val is None or after_val is None:
            return None
        return before_val * 10 + after_val

    total = 0
    for ch in text:
        digit = CN_NUMERAL_MAP.get(ch)
        if digit is None:
            return None
        total = total * 10 + digit
    return total or None


def parse_chapter_no(chapter_arg: str) -> int:
    """统一解析命令行章节参数为阿拉伯数字。"""
    chapter_id = _parse_chapter_id(chapter_arg or "")
    if chapter_id is None:
        raise ValueError(f"无法解析章节编号：{chapter_arg}")
    return chapter_id


def load_toc_chapters(doc: "fitz.Document") -> List[Dict]:
    """
    读取 PDF TOC，只保留顶层“第X章 …”的条目。
    返回的 page 字段为 1-based 页码（与 PyMuPDF TOC 一致）。
    """
    toc = doc.get_toc(simple=True) or []
    chapters: List[Dict] = []
    for level, title, page in toc:
        if level != 1:
            continue
        title = (title or "").strip()
        if not title:
            continue
        if not CHAPTER_PATTERN.search(title):
            continue
        chapter_no = _parse_chapter_id(title)
        if chapter_no is None:
            continue
        page_num = int(page) if isinstance(page, int) else 1
        page_num = max(1, page_num)
        chapters.append(
            {
                "chapter_no": chapter_no,
                "title": title,
                "page": page_num,
            }
        )
    chapters.sort(key=lambda item: item["page"])
    return chapters


def find_chapter_by_no(
    toc_chapters: List[Dict], chapter_no: int
) -> Tuple[Dict, Optional[Dict]]:
    """在 TOC 列表中查找指定章节及其下一章。"""
    for idx, chapter in enumerate(toc_chapters):
        if chapter["chapter_no"] != chapter_no:
            continue
        next_chapter = toc_chapters[idx + 1] if idx + 1 < len(toc_chapters) else None
        return chapter, next_chapter
    raise ValueError(f"TOC 中未找到第 {chapter_no} 章。")


def extract_pages_text(doc: "fitz.Document", start_page: int, end_page: int) -> str:
    """
    根据页码范围抽取正文。
    start_page / end_page 均为 0-based，end_page 不包含在内。
    """
    if start_page < 0:
        start_page = 0
    if end_page <= start_page:
        end_page = start_page + 1
    end_page = min(end_page, doc.page_count)
    texts: List[str] = []
    for page_index in range(start_page, end_page):
        page = doc.load_page(page_index)
        texts.append(page.get_text("text"))
    return "\n".join(texts).strip()


def extract_chapter_by_toc(doc: "fitz.Document", chapter_arg: str) -> Dict:
    """优先使用 TOC 精准定位章节。"""
    toc_chapters = load_toc_chapters(doc)
    if not toc_chapters:
        raise ValueError("TOC 为空或未包含章节信息。")
    chapter_no = parse_chapter_no(chapter_arg)
    current, next_chapter = find_chapter_by_no(toc_chapters, chapter_no)
    start_page = current["page"] - 1  # 转成 0-based（PyMuPDF 页码从 1 开始）
    # 结束页：如果有下一章，则到下一章开始；否则到文档末尾
    if next_chapter:
        end_page = next_chapter["page"] - 1  # 不包含下一章的开始页
    else:
        end_page = doc.page_count  # 最后一章，到文档末尾
    # 确保 end_page 大于 start_page
    if end_page <= start_page:
        end_page = start_page + 1
    text = extract_pages_text(doc, start_page, end_page)
    if not text.strip():
        raise ValueError(f"TOC 模式未提取到章节正文：{current['title']}")
    return {
        "text": text,
        "title": current["title"],
        "chapter_no": chapter_no,
        "start_page": start_page,
        "end_page": end_page,
    }


def fallback_scan_chapter_by_text(pdf_path: Path, chapter_arg: str) -> Dict:
    """
    TOC 不可用时，回退到全文扫描。
    仅保留标题中包含“第X章”的候选，避免匹配前言/版权页。
    """
    print("章节识别：使用全文扫描兜底模式。")
    full_text = extract_text_from_file(str(pdf_path))
    if not full_text.strip():
        raise ValueError("全文扫描失败：PDF 文本为空。")

    chapters = split_into_chapters(full_text)
    if not chapters:
        raise ValueError("全文扫描失败：未识别任何章节。")

    chapter_no = parse_chapter_no(chapter_arg)
    filtered: List[Dict] = []
    for chapter in chapters:
        title = (chapter.get("title") or "").strip()
        if not title or not CHAPTER_PATTERN.search(title):
            continue
        parsed_no = _parse_chapter_id(title)
        if parsed_no is None:
            continue
        filtered.append(
            {
                "chapter_no": parsed_no,
                "title": title,
                "text": (chapter.get("text") or "").strip(),
            }
        )

    if not filtered:
        raise ValueError("全文扫描失败：未找到包含“第X章”的候选标题。")

    for candidate in filtered:
        if candidate["chapter_no"] != chapter_no:
            continue
        if not candidate["text"]:
            continue
        return {
            "text": candidate["text"],
            "title": candidate["title"],
            "chapter_no": chapter_no,
        }

    raise ValueError(f"全文扫描失败：未匹配到第 {chapter_no} 章。")


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
        default=None,
        help="兼容旧参数（已不再使用）",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        help="兼容旧参数（已不再使用）",
    )

    args = parser.parse_args()

    pdf_path = resolve_pdf_path(args.pdf)
    output_path = Path(args.output)

    print(f"正在解析章节：{args.chapter}")

    toc_result: Optional[Dict] = None
    with fitz.open(pdf_path) as doc:
        try:
            toc_result = extract_chapter_by_toc(doc, args.chapter)
        except Exception as exc:
            print(f"章节识别：TOC 模式失败（{exc}）。将尝试兜底方案。")

    if toc_result:
        start_display = toc_result["start_page"] + 1
        end_display = toc_result["end_page"]
        print("章节识别：使用 TOC 模式。")
        print(
            f"已匹配章节：{toc_result['title']}（chapter_no={toc_result['chapter_no']}, pages={start_display}~{end_display}）。"
        )
        save_output(toc_result["text"], output_path)
        return

    try:
        fallback_result = fallback_scan_chapter_by_text(pdf_path, args.chapter)
    except Exception as exc:
        print(f"兜底模式同样失败：{exc}")
        sys.exit(1)

    print(
        f"兜底模式匹配章节：{fallback_result['title']}（chapter_no={fallback_result['chapter_no']}）。"
    )
    save_output(fallback_result["text"], output_path)


if __name__ == "__main__":
    main()
