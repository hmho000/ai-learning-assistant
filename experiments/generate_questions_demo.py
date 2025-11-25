"""
generate_questions_demo.py
--------------------------

通用题库生成脚本：
- 输入任意学科文本，自动识别主题与章节
- 生成 8~12 道选择题与 8~12 道填空题
- 输出统一 JSON 结构
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

DEFAULT_INPUT_PATH = Path("experiments/output/chapter_text.txt")
DEFAULT_OUTPUT_PATH = Path("experiments/output/chapter_questions.json")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_API_KEY = "sk-3242989c595b4e0e9798190133d80bf5"


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到输入文本文件：{path}")
    text = path.read_text(encoding="utf-8")
    print(f"已读取文本，长度 {len(text)} 字符。")
    return text


def build_prompt(
    chapter_text: str,
    chapter_index: Optional[int] = None,
    chapter_hint: Optional[str] = None,
) -> str:
    context_lines = []
    if chapter_index is not None:
        context_lines.append(f"- 章节编号提示：{chapter_index}")
    if chapter_hint:
        context_lines.append(f"- 文档/章节线索：{chapter_hint}")
    context_block = "\n".join(context_lines)

    prompt = f"""
你是一名专业的教育测评专家。
请仔细阅读下面的文档内容，自动完成：
1. 识别所属学科或主题（如：计算机网络、线性代数、人工智能、历史、化学……）
2. 识别最能概括该段内容的章节标题（无需与原文完全相同，可自行概括）
3. 提炼 3~6 个核心知识点，覆盖全文主要内容
4. 基于这些知识点生成题库标题（专业、简洁）、题库描述（2~3 句话）
5. 命制 8~12 道单选题（multiple_choice）与 8~12 道填空题（fill_in_blank）

题目要求：
- 必须可以从文本内容推导，避免凭空创作
- 尽量覆盖不同的知识点与技能层次
- 每道题附带正确答案与简洁、明确的解析
- 语言保持专业、严谨，禁止出现“见上文”“自行总结”等模糊描述

输出必须是合法 JSON，严格遵循以下结构（不得包含额外注释或文字）：
{{
  "meta": {{
    "chapter_index": <int，缺省时请填 1>,
    "chapter_title": "<自动识别的章节标题>",
    "quiz_title": "<自动生成的题库标题>",
    "quiz_description": "<2~3 句简介>"
  }},
  "multiple_choice": [
    {{
      "id": 1,
      "question": "题干……",
      "options": ["A. ……", "B. ……", "C. ……", "D. ……"],
      "answer": "B",
      "explanation": "解析……"
    }}
  ],
  "fill_in_blank": [
    {{
      "id": 1,
      "question": "题干……",
      "answer": "标准答案",
      "explanation": "解析……"
    }}
  ]
}}

请确保 multiple_choice 与 fill_in_blank 数组长度都在 8~12 之间。
禁止输出 markdown 代码块标记（```），禁止输出任何与 JSON 无关的文字。

{context_block}

【原始文档内容开始】
{chapter_text}
【原始文档内容结束】
"""
    return prompt.strip()


def call_deepseek(
    api_key: str,
    model: str,
    prompt: str,
    temperature: float = 0.3,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一名严谨的教育测评专家，擅长根据任意学科文本命制高质量题库。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "stream": False,
    }
    print(f"正在调用 DeepSeek API，模型：{model} ……")
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=300)
    if resp.status_code != 200:
        raise RuntimeError(
            f"DeepSeek API 调用失败，HTTP {resp.status_code}：{resp.text}"
        )

    resp_json = resp.json()
    try:
        return resp_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"无法从 DeepSeek 响应中解析 content：{resp_json}") from exc


def parse_questions_json(raw_content: str) -> Dict[str, Any]:
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "").replace("JSON\n", "")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"解析 JSON 失败，请手动检查模型输出。\n错误：{e}\n原始内容：\n{text}"
        ) from e

    if "meta" not in data:
        print("警告：JSON 中缺少 meta 字段。")
    for key in ("multiple_choice", "fill_in_blank"):
        if key not in data or not isinstance(data[key], list):
            print(f"警告：JSON 中缺少 {key} 数组。")
    return data


def save_output_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"题目已保存到：{path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="通用 AI 出题 Demo 脚本")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_PATH),
        help="章节或文档文本文件路径（默认 experiments/output/chapter_text.txt）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help="题目输出 JSON 路径（默认 experiments/output/chapter_questions.json）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="DeepSeek 模型名称（例如 deepseek-chat / deepseek-reasoner）",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="DeepSeek API Key（可通过参数或 DEEPSEEK_API_KEY 环境变量提供）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="采样温度，默认 0.3",
    )
    parser.add_argument(
        "--chapter-index",
        type=int,
        default=None,
        help="章节编号提示（可选，默认 1）",
    )
    parser.add_argument(
        "--chapter-hint",
        type=str,
        default=None,
        help="章节或文档标题提示（可选）",
    )
    # 兼容旧版参数
    parser.add_argument(
        "--chapter-id",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--chapter-title",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY") or DEFAULT_API_KEY
    if not api_key:
        raise RuntimeError(
            "未提供 DeepSeek API Key，请通过 --api-key 或 DEEPSEEK_API_KEY 环境变量设置。"
        )

    input_path = Path(args.input)
    output_path = Path(args.output)

    chapter_text = load_text(input_path)
    # 兼容旧版 run_all.py 的参数
    effective_chapter_index = (
        args.chapter_index
        if args.chapter_index is not None
        else args.chapter_id
        if args.chapter_id is not None
        else 1
    )
    effective_chapter_hint = args.chapter_hint or args.chapter_title

    prompt = build_prompt(
        chapter_text,
        chapter_index=effective_chapter_index,
        chapter_hint=effective_chapter_hint,
    )
    raw_content = call_deepseek(
        api_key=api_key,
        model=args.model,
        prompt=prompt,
        temperature=args.temperature,
    )
    questions = parse_questions_json(raw_content)
    save_output_json(questions, output_path)


if __name__ == "__main__":
    main()

