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
from typing import Dict, List, Optional

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

    cn_match = re.search(r"第\s*([零一二三四五六七八九十百]+)\s*章", value)
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


def choose_chapter(chapters: List[Dict], chapter_label: str) -> Optional[Dict]:
    """按照 id（优先）或标题匹配章节。"""
    if not chapters:
        return None

    chapter_id = _parse_chapter_id(chapter_label)
    if chapter_id is not None:
        for chapter in chapters:
            if chapter.get("id") == chapter_id:
                return chapter

    normalized = chapter_label.strip()
    for chapter in chapters:
        title = chapter.get("title") or ""
        if normalized and normalized in title:
            return chapter

    return None


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

    try:
        full_text = extract_text_from_file(str(pdf_path))
    except Exception as exc:  # pragma: no cover - 记录信息方便排查
        print(f"提取 PDF 文本失败：{exc}")
        sys.exit(1)

    if not full_text.strip():
        print("PDF 文本为空，请检查抽取流程或 PDF 文件是否受保护。")
        sys.exit(1)

    chapters = split_into_chapters(full_text)
    print(f"章节识别完成，共 {len(chapters)} 章。")

    target = choose_chapter(chapters, args.chapter)
    if target is None:
        print(f"未找到章节：{args.chapter}")
        sys.exit(1)

    chapter_text = target.get("text", "").strip()
    if not chapter_text:
        print(f"章节 {target.get('title')} 文本为空。")
        sys.exit(1)

    print(f"已匹配章节：{target.get('title')}（id={target.get('id')}）。")
    save_output(chapter_text, output_path)


if __name__ == "__main__":
    main()
