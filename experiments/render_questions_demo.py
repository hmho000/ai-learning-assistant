"""
render_questions_demo.py
------------------------

读取题目 JSON，将其渲染为 Markdown，便于人工预览、校对。
同时自动更新前端 manifest.json，实现章节信息的动态管理。

支持从 JSON 的 meta 字段自动读取章节信息，实现全自动流程。
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


DEFAULT_INPUT_PATH = Path("experiments/output/chapter_2_questions.json")

# 前端根目录路径
REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = REPO_ROOT / "frontend"
MANIFEST_PATH = FRONTEND_ROOT / "public" / "questions" / "manifest.json"


def load_questions(path: Path) -> Dict[str, Any]:
    """
    加载题目 JSON，返回包含 meta 和题目的完整数据。

    Returns:
        包含 meta、multiple_choice、fill_in_blank 的字典
    """
    if not path.exists():
        raise FileNotFoundError(f"找不到题目 JSON 文件：{path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    meta = data.get("meta", {}) or {}
    multiple_choice = data.get("multiple_choice", [])
    fill_in_blank = data.get("fill_in_blank", [])

    print(
        f"已从 {path} 读取 JSON，包含 {len(multiple_choice)} 道选择题，"
        f"{len(fill_in_blank)} 道填空题。"
    )

    if meta:
        print(f"已读取元数据：章节 {meta.get('chapter_index', '?')} - {meta.get('chapter_title', '未知')}")
    else:
        print("警告：JSON 中未找到 meta 字段，将使用默认值。")

    return {
        "meta": meta,
        "multiple_choice": multiple_choice,
        "fill_in_blank": fill_in_blank,
    }


def render_choice_question(item: Dict[str, Any], show_answer: bool) -> str:
    lines = [
        f"**第 {item.get('id', '?')} 题**  ",
        item.get("question", "").strip(),
        "",
    ]
    options = item.get("options", [])
    for opt in options:
        lines.append(f"{opt.strip()}  ")
    if show_answer:
        lines.extend(
            [
                "",
                f"> 正确答案：{item.get('answer', '').strip()}  ",
                f"> 解析：{item.get('explanation', '').strip()}",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_blank_question(item: Dict[str, Any], show_answer: bool) -> str:
    lines = [
        f"**第 {item.get('id', '?')} 题**  ",
        item.get("question", "").strip(),
    ]
    if show_answer:
        lines.extend(
            [
                "",
                f"> 正确答案：{item.get('answer', '').strip()}  ",
                f"> 解析：{item.get('explanation', '').strip()}",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_markdown(
    questions: Dict[str, Any],
    show_answer: bool,
    quiz_title: Optional[str] = None,
    quiz_description: Optional[str] = None,
) -> str:
    """
    渲染 Markdown，使用 meta 信息生成标题和描述。

    Args:
        questions: 包含 meta、multiple_choice、fill_in_blank 的字典
        show_answer: 是否显示答案
        quiz_title: 题库标题（优先使用，否则从 meta 读取）
        quiz_description: 题库描述（优先使用，否则从 meta 读取）
    """
    meta = questions.get("meta", {}) or {}

    # 确定标题和描述
    effective_title = quiz_title or meta.get("quiz_title") or "自动生成的练习题"
    effective_description = quiz_description or meta.get("quiz_description") or ""

    lines: List[str] = [
        f"# {effective_title}",
        "",
        "本文件由 AI 脚本自动生成，用于预览与校对。",
        "",
    ]

    # 如果有描述，添加为 blockquote
    if effective_description:
        lines.append(f"> {effective_description}")
        lines.append("")

    lines.extend(
        [
            "## 一、选择题（Multiple Choice）",
            "",
        ]
    )

    multiple_choice = questions.get("multiple_choice", [])
    if multiple_choice:
        for item in multiple_choice:
            lines.append(render_choice_question(item, show_answer))
            lines.append("")
    else:
        lines.append("（当前类型暂无题目）")
        lines.append("")

    lines.extend(
        [
            "## 二、填空题（Fill in the Blank）",
            "",
        ]
    )

    fill_in_blank = questions.get("fill_in_blank", [])
    if fill_in_blank:
        for item in fill_in_blank:
            lines.append(render_blank_question(item, show_answer))
            lines.append("")
    else:
        lines.append("（当前类型暂无题目）")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def update_manifest(
    manifest_path: Path,
    chapter_id: int,
    chapter_title: str,
    markdown_file: Path,
    chapter_desc: Optional[str] = None,
) -> None:
    """
    更新或创建 manifest.json，添加或更新章节信息。

    Args:
        manifest_path: manifest.json 的完整路径
        chapter_id: 章节 ID（整数）
        chapter_title: 章节标题，例如 "第2章 线性表"
        markdown_file: Markdown 文件的完整路径（用于提取文件名）
        chapter_desc: 章节描述（可选）
    """
    # 如果 manifest 不存在，创建默认结构
    if not manifest_path.exists():
        manifest_data = {
            "course": "数据结构",
            "chapters": [],
        }
    else:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 确保 chapters 字段存在
    if "chapters" not in manifest_data:
        manifest_data["chapters"] = []

    # 生成 shortLabel
    short_label = f"第{chapter_id}章"

    # 提取文件名（只保存相对文件名）
    file_name = markdown_file.name

    # 查找是否已存在相同 id 的章节
    existing_index = None
    for idx, ch in enumerate(manifest_data["chapters"]):
        if ch.get("id") == chapter_id:
            existing_index = idx
            break

    chapter_entry = {
        "id": chapter_id,
        "label": chapter_title,
        "shortLabel": short_label,
        "file": file_name,
        "description": chapter_desc or "",
    }

    if existing_index is not None:
        # 更新现有章节
        manifest_data["chapters"][existing_index] = chapter_entry
        print(f"已更新章节 {chapter_id} 的信息。")
    else:
        # 新增章节
        manifest_data["chapters"].append(chapter_entry)
        print(f"已新增章节 {chapter_id} 到清单。")

    # 按 id 排序
    manifest_data["chapters"].sort(key=lambda x: x.get("id", 0))

    # 确保目录存在
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # 写回文件
    manifest_path.write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已更新章节清单：{manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="渲染题目 JSON 为 Markdown，并自动更新前端 manifest.json（支持从 meta 自动读取信息）"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_PATH),
        help="题目 JSON 文件路径（默认 experiments/output/chapter_2_questions.json）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 Markdown 路径（默认打印到 stdout）",
    )
    parser.add_argument(
        "--show-answer",
        action="store_true",
        help="输出时显示答案与解析",
    )
    parser.add_argument(
        "--chapter-id",
        type=int,
        default=None,
        help="章节 ID（可选，用于 override 或兜底，例如 2）",
    )
    parser.add_argument(
        "--chapter-title",
        type=str,
        default=None,
        help="章节标题（可选，用于 override，例如 '第2章 线性表'）",
    )
    parser.add_argument(
        "--chapter-desc",
        type=str,
        default=None,
        help="章节描述（可选，用于 override）",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    questions_data = load_questions(input_path)

    meta = questions_data.get("meta", {}) or {}

    # 确定有效的章节信息（优先级：命令行参数 > meta > 默认值）
    effective_chapter_id = (
        args.chapter_id
        or meta.get("chapter_index")
        or 1
    )
    effective_chapter_title = (
        args.chapter_title
        or meta.get("chapter_title")
        or f"第{effective_chapter_id}章"
    )
    effective_chapter_desc = (
        args.chapter_desc
        or meta.get("quiz_description")
        or ""
    )

    # 确定题库标题和描述（用于 Markdown）
    quiz_title = meta.get("quiz_title")
    quiz_description = meta.get("quiz_description")

    # 渲染 Markdown
    markdown = render_markdown(
        questions_data,
        args.show_answer,
        quiz_title=quiz_title,
        quiz_description=quiz_description,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Markdown 已保存到：{output_path}")

        # 更新 manifest.json
        update_manifest(
            manifest_path=MANIFEST_PATH,
            chapter_id=effective_chapter_id,
            chapter_title=effective_chapter_title,
            markdown_file=output_path,
            chapter_desc=effective_chapter_desc,
        )
    else:
        print(markdown)
        print(
            "\n注意：未指定 --output 时，不会更新 manifest.json。"
            "如需自动更新清单，请提供 --output 参数。"
        )


if __name__ == "__main__":
    main()
