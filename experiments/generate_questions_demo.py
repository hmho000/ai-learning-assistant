"""
generate_questions_demo.py
--------------------------

根据教材章节文本，调用 DeepSeek Chat API 自动生成选择题和填空题。

用法示例：
    python experiments/generate_questions_demo.py \
        --input experiments/output/chapter_2.txt \
        --output experiments/output/chapter_2_questions.json \
        --model deepseek-chat

环境要求：
    pip install requests
    并在环境变量中设置：
        DEEPSEEK_API_KEY=你的密钥
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests

DEFAULT_INPUT_PATH = Path("experiments/output/chapter_2.txt")
DEFAULT_OUTPUT_PATH = Path("experiments/output/chapter_2_questions.json")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"  # 你也可以改成 deepseek-reasoner 等
DEFAULT_API_KEY = "sk-3242989c595b4e0e9798190133d80bf5"


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到输入文本文件：{path}")
    text = path.read_text(encoding="utf-8")
    print(f"已读取章节文本，长度 {len(text)} 字符。")
    return text


def build_prompt(chapter_text: str) -> str:
    """
    构造给 DeepSeek 的用户提示词。
    要求它严格输出 JSON，方便后续解析。
    """
    prompt = f"""
你是一名中国大学《数据结构》课程的教师，现在要根据下面的教材内容出题。

【教材内容开始】
{chapter_text}
【教材内容结束】

请你根据这部分内容，面向 **大二计算机专业学生**，生成：

1. 5 道单选题（multiple_choice）
2. 5 道填空题（fill_in_blank）

要求：
- 题目紧扣教材内容，不要出偏题。
- 每道题附带简明扼要的解析（explanation），突出考察的知识点。
- 难度控制在基础～中等。
- 所有输出 **必须是合法 JSON**，不要包含任何多余说明文字。

JSON 输出格式严格如下（字段名不要改）：

{{
  "multiple_choice": [
    {{
      "id": 1,
      "question": "题干……",
      "options": ["A. ……", "B. ……", "C. ……", "D. ……"],
      "answer": "C",
      "explanation": "为什么选 C 的简要说明。"
    }}
  ],
  "fill_in_blank": [
    {{
      "id": 1,
      "question": "顺序表的逻辑结构是__________。",
      "answer": "线性结构",
      "explanation": "简要说明。"
    }}
  ]
}}

特别注意：
- 顶层必须是一个 JSON 对象。
- 不要输出任何与 JSON 无关的文字，比如“好的，下面是题目”“解析如下”等。
- 不要使用注释。
- 不要把 JSON 放在代码块（例如 ```json）里。
"""
    return prompt.strip()


def call_deepseek(
    api_key: str,
    model: str,
    prompt: str,
    temperature: float = 0.4,
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
                "content": "你是一名严谨的中国大学数据结构老师，擅长根据教材内容命题。",
            },
            {
                "role": "user",
                "content": prompt,
            },
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
        content = resp_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"无法从 DeepSeek 响应中解析 content：{resp_json}") from e

    print("已收到 DeepSeek 响应。")
    return content


def parse_questions_json(raw_content: str) -> Dict[str, Any]:
    """
    尝试把模型输出解析成 JSON。
    如果解析失败，则抛出异常，方便你手动检查原始输出。
    """
    # 有些模型可能会在前后混入奇怪字符，这里简单做一次 strip
    text = raw_content.strip()

    # 防止模型不听话输出 ```json ... ``` 这种格式
    if text.startswith("```"):
        # 粗暴去掉代码块包裹
        text = text.strip("`")
        # 如果里面带有 "json\n" 之类前缀，继续处理
        text = text.replace("json\n", "").replace("JSON\n", "")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"解析 JSON 失败，请手动检查模型输出。\n错误：{e}\n原始内容：\n{text}"
        ) from e

    # 简单结构校验
    if "multiple_choice" not in data or "fill_in_blank" not in data:
        print("警告：JSON 中缺少 multiple_choice 或 fill_in_blank 字段。")
    return data


def save_output_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"题目已保存到：{path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="基于 DeepSeek 的 AI 出题 Demo 脚本")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_PATH),
        help="章节文本文件路径（默认 experiments/output/chapter_2.txt）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help="题目输出 JSON 路径（默认 experiments/output/chapter_2_questions.json）",
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
        default=DEFAULT_API_KEY,
        help="DeepSeek API Key（可通过参数、环境变量或脚本内默认值提供）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.4,
        help="采样温度，默认为 0.4（偏稳重一点）",
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
    prompt = build_prompt(chapter_text)
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
