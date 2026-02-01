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
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    from .ocr_demo import ocr_image
except ImportError:
    from ocr_demo import ocr_image

# 默认输入/输出路径（一般由 run_all.py 显式传入）
DEFAULT_INPUT_PATH = Path("experiments/output/chapter_text.txt")
DEFAULT_OUTPUT_PATH = Path("experiments/output/chapter_questions.json")

# DeepSeek API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
# 出于安全考虑，这里不再硬编码真实 API Key，建议使用环境变量或命令行参数

# 题目数量下限（仅用于报警提示，不会自动补题）
MIN_QUESTIONS_PER_TYPE = 8

# ---------------------------
#  编号题过滤规则（算法2.16 / 图3.5 / 例1.1 等）
# ---------------------------

ALGO_REF_PATTERN = re.compile(
    r"(算法\s*\d+(\.\d+)?)|"
    r"(例\s*\d+(\.\d+)?)|"
    r"(案例\s*\d+(\.\d+)?)|"
    r"(图\s*\d+(\.\d+)?)|"
    r"(表\s*\d+(\.\d+)?)"
)


def is_bad_referenced_question(q: Dict[str, Any]) -> bool:
    """
    判定题干是否严重依赖“算法/例/图/表编号”，例如：
    - 算法2.16中……
    - 图3.5 所示的结构……
    这类题离开原书编号后，学生无法独立作答，因此不推荐保留。
    """
    text = (q.get("question") or "").strip()
    if not text:
        return True
    return bool(ALGO_REF_PATTERN.search(text))


def filter_questions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    对模型返回的题目做质量过滤：
    - 删除严重依赖编号（算法x.x / 例x.x / 图x.x / 表x.x）的题目

    若过滤后数量不足 MIN_QUESTIONS_PER_TYPE，仅给出警告，不会自动补题。
    """
    mc: List[Dict[str, Any]] = payload.get("multiple_choice") or []
    fb: List[Dict[str, Any]] = payload.get("fill_in_blank") or []

    filtered_mc = [q for q in mc if not is_bad_referenced_question(q)]
    filtered_fb = [q for q in fb if not is_bad_referenced_question(q)]

    removed_mc = len(mc) - len(filtered_mc)
    removed_fb = len(fb) - len(filtered_fb)

    if removed_mc or removed_fb:
        print(
            f"[filter] 移除了 {removed_mc} 道选择题、{removed_fb} 道填空题"
            "（含算法/例/图/表编号）。"
        )

    payload["multiple_choice"] = filtered_mc
    payload["fill_in_blank"] = filtered_fb

    # 数量检查（仅报警）
    if len(filtered_mc) < MIN_QUESTIONS_PER_TYPE:
        print(
            f"[警告] 选择题数量少于 {MIN_QUESTIONS_PER_TYPE} 道"
            f"（当前 {len(filtered_mc)} 道），可能是过滤掉过多编号题导致的。"
        )
    if len(filtered_fb) < MIN_QUESTIONS_PER_TYPE:
        print(
            f"[警告] 填空题数量少于 {MIN_QUESTIONS_PER_TYPE} 道"
            f"（当前 {len(filtered_fb)} 道），可能是过滤掉过多编号题导致的。"
        )

    return payload


# ---------------------------
#  基础工具函数
# ---------------------------


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到输入文件：{path}")
    
    suffix = path.suffix.lower()
    
    # 图片扩展名列表
    image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
    
    if suffix in image_exts:
        print(f"正在对图片进行 OCR 识别：{path} ...")
        text = ocr_image(path)
        print(f"OCR 识别完成，长度 {len(text)} 字符。")
    else:
        # 默认当做文本处理
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # 尝试 GBK
            text = path.read_text(encoding="gbk", errors="ignore")
            
        print(f"已读取文本，长度 {len(text)} 字符。")
    
    return text


def build_prompt(
    chapter_text: str,
    chapter_index: Optional[int] = None,
    chapter_hint: Optional[str] = None,
) -> str:
    """
    构造给 DeepSeek 的用户 Prompt。
    - 通用学科，不再写死为《数据结构》
    - 自动识别章节标题 / 题库标题 / 描述
    - 要求生成 8~12 道选择题 & 8~12 道填空题
    """
    context_lines: List[str] = []
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
- 题目必须自包含，不能依赖教材中的“算法 2.16”“图 3-5”“例 4.2”等编号。
  如需引用，请使用自然语言描述算法/图表的内容，而不是编号。

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

要求：
- multiple_choice 与 fill_in_blank 数组长度都应在 8~12 之间。
- 禁止输出 markdown 代码块标记（```），禁止输出任何与 JSON 无关的文字。

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
    """
    调用 DeepSeek Chat Completion API，返回模型输出的 content 字符串。
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一名严谨的教育测评专家，"
                    "擅长根据任意学科文本命制高质量题库。"
                ),
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
    """
    解析模型输出的 JSON，并做一层质量过滤（去掉编号题）。
    """
    text = raw_content.strip()
    # 兼容模型偶尔返回 ```json ... ``` 的情况
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

    # 做一层编号题过滤
    data = filter_questions(data)

    return data


def save_output_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"题目已保存到：{path}")


# ---------------------------
#  CLI 入口
# ---------------------------


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
        help="采样温度，默认 0.3（偏稳重）",
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
    # 兼容旧版 run_all.py 的参数名
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

    from dotenv import load_dotenv
    load_dotenv(override=True)

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key.strip() == "sk-your_api_key_here":
        raise RuntimeError(
            "未提供有效的 DeepSeek API Key，请通过 --api-key 参数提供，或在 .env 文件中配置 DEEPSEEK_API_KEY。"
        )

    input_path = Path(args.input)
    output_path = Path(args.output)

    chapter_text = load_text(input_path)

    # 兼容旧版参数：优先使用新参数，其次旧参数，最后默认 1
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
