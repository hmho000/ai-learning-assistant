"""
render_questions_demo.py
------------------------

读取题目 JSON，将其渲染为 Markdown，便于人工预览、校对。
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any


DEFAULT_INPUT_PATH = Path("experiments/output/chapter_2_questions.json")


def load_questions(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"找不到题目 JSON 文件：{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    multiple_choice = data.get("multiple_choice", [])
    fill_in_blank = data.get("fill_in_blank", [])
    print(
        f"已从 {path} 读取 JSON，包含 {len(multiple_choice)} 道选择题，"
        f"{len(fill_in_blank)} 道填空题。"
    )
    return {"multiple_choice": multiple_choice, "fill_in_blank": fill_in_blank}


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
    questions: Dict[str, List[Dict[str, Any]]], show_answer: bool
) -> str:
    lines: List[str] = [
        "# 自动生成的练习题",
        "",
        "本文件由 AI 脚本自动生成，用于预览与校对。",
        "",
        "## 一、选择题（Multiple Choice）",
        "",
    ]

    multiple_choice = questions["multiple_choice"]
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

    fill_in_blank = questions["fill_in_blank"]
    if fill_in_blank:
        for item in fill_in_blank:
            lines.append(render_blank_question(item, show_answer))
            lines.append("")
    else:
        lines.append("（当前类型暂无题目）")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染题目 JSON 为 Markdown")
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

    args = parser.parse_args()

    input_path = Path(args.input)
    questions = load_questions(input_path)
    markdown = render_markdown(questions, args.show_answer)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Markdown 已保存到：{output_path}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()

