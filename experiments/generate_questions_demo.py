"""
generate_questions_demo.py
--------------------------

根据教材章节文本，调用 DeepSeek Chat API 自动生成选择题和填空题。
同时自动生成章节元数据（meta），包括章节标题、题库标题和描述。

用法示例：
    python experiments/generate_questions_demo.py \
        --input experiments/output/ch2_clean.txt \
        --output experiments/output/chapter_2_questions.json \
        --chapter-id 2 \
        --chapter-title "第2章 线性表"

环境要求：
    pip install requests
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

DEFAULT_INPUT_PATH = Path("experiments/output/chapter_2.txt")
DEFAULT_OUTPUT_PATH = Path("experiments/output/chapter_2_questions.json")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_API_KEY = "sk-3242989c595b4e0e9798190133d80bf5"
MIN_QUESTIONS_PER_TYPE = 5  # 每种题型最少题目数量

# 用于检测题干中是否包含算法/例题/图表编号的正则表达式
ALGO_REF_PATTERN = re.compile(
    r"(算法\s*\d+(\.\d+)?)|"
    r"(例\s*\d+(\.\d+)?)|"
    r"(案例\s*\d+(\.\d+)?)|"
    r"(图\s*\d+(\.\d+)?)|"
    r"(表\s*\d+(\.\d+)?)"
)


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到输入文本文件：{path}")
    text = path.read_text(encoding="utf-8")
    print(f"已读取章节文本，长度 {len(text)} 字符。")
    return text


def build_prompt(
    chapter_text: str,
    chapter_id: Optional[int] = None,
    chapter_title: Optional[str] = None,
    is_supplement: bool = False,
) -> str:
    """
    构造给 DeepSeek 的用户提示词。
    要求它严格输出 JSON，包含 meta 元数据和题目。

    Args:
        chapter_text: 章节文本内容
        chapter_id: 可选的章节编号（用于提示模型）
        chapter_title: 可选的章节标题（用于提示模型）
    """
    chapter_context = ""
    if chapter_id is not None or chapter_title is not None:
        parts = []
        if chapter_id is not None:
            parts.append(f"第 {chapter_id} 章")
        if chapter_title:
            parts.append(f"《{chapter_title}》")
        chapter_context = f"\n\n本题库对应教材中的{' '.join(parts)}。\n"
    else:
        chapter_context = (
            "\n\n如果没有提供章节编号和标题，请根据文本内容自行判断并填写 meta 中的章节信息。\n"
        )

    supplement_note = ""
    if is_supplement:
        supplement_note = "\n\n注意：这是补充出题请求，请确保新生成的题目与之前已生成的题目不重复，且同样遵循所有出题质量要求。\n"

    prompt = f"""
你是一名中国大学《数据结构》课程的教师，现在要根据下面的教材内容出题。

【教材内容开始】
{chapter_text}
【教材内容结束】
{chapter_context}{supplement_note}
请你根据这部分内容，面向 **大二计算机专业学生**，生成：

1. 章节元数据（meta）：包括章节编号、章节标题、题库标题和描述
2. 5 道单选题（multiple_choice）
3. 5 道填空题（fill_in_blank）

要求：
- 题目紧扣教材内容，不要出偏题。
- 每道题附带简明扼要的解析（explanation），突出考察的知识点。
- 难度控制在基础～中等。
- 所有输出 **必须是合法 JSON**，不要包含任何多余说明文字。

出题质量要求（重要）：
- 出题必须**自包含**，不要依赖教材中的"算法编号、例题编号、图表编号"等信息。
  - **禁止**在题干中出现诸如"算法3.22""算法 3.21""例3.2""案例3.4""图3.5""表3.2"等表述。
  - 如果必须引用某个算法，请改写成"栈的算符优先表达式求值算法""舞伴配对问题中的队列算法"等，使用**概念名称**而不是编号。
  - 如果某个算法或例题在文本中只被略微提及（只有编号，没有完整解释），**不要**针对它出题。
- 尽量覆盖本章节的**多个知识点**，不要把所有题目都集中在同一个算法或例题上。
  - 建议至少覆盖 4~6 个不同的核心概念（例如：栈的基本操作、表达式求值、括号匹配、舞伴问题、时间/空间复杂度等）。
  - 同一个知识点不要出超过 2 道题，出多道题时要换角度（比如一题考概念，一题考应用）。
- 所有题目都要**可以由本段文本直接推理或查找到答案**，不要考"只在别处出现、当前文本里没有的信息"。

JSON 输出格式严格如下（字段名不要改）：

{{
  "meta": {{
    "chapter_index": 2,
    "chapter_title": "第2章 线性表",
    "quiz_title": "第2章·线性表——顺序表与链表综合练习",
    "quiz_description": "本题库围绕线性表的基本概念、顺序表与链表的表示与操作以及有序表合并等内容设计，适合作为本章学习后的巩固与自测。"
  }},
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
- **必须包含 meta 字段**，且内部字段名严格是：
  - chapter_index (int): 章节编号
  - chapter_title (string): 教材中这章的正式标题，例如 "第2章 线性表"
  - quiz_title (string): 这个题库本身的标题，适合放在页面/Markdown 的 H1，例如 "第2章·线性表——顺序表与链表综合练习"
  - quiz_description (string): 2-3 句话，说明本题库涵盖的知识点 & 适用人群，用于页面顶部的小字/manifest 描述
- 仍然必须有 multiple_choice 和 fill_in_blank 数组。
- 不要输出任何与 JSON 无关的文字，比如"好的，下面是题目""解析如下"等。
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


def is_bad_referenced_question(q: Dict[str, Any]) -> bool:
    """
    判断题干是否严重依赖"算法/例/图/表编号"，属于不推荐保留的题目。
    当前策略：只要题干里出现类似"算法3.22""例3.2""图3.5"之类就标记为不合格。

    Args:
        q: 题目字典，包含 question 字段

    Returns:
        True 表示题目不合格（包含编号引用），False 表示合格
    """
    text = (q.get("question") or "").strip()
    if not text:
        return True
    return bool(ALGO_REF_PATTERN.search(text))


def filter_questions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    对模型返回的题目做一次简单质量过滤：
    - 删除严重依赖编号的题目（算法x.x / 例x.x / 图x.x / 表x.x）

    未来可以在此处增加更多规则：
    - 统计题干中重复出现的核心词，限制单个关键词的题目数量不超过 2 道
    - 对题干文本做简单归一化（去标点、小写），避免几乎一模一样的题目重复出现
    - 根据 meta 中的章节标题，提示模型尽量覆盖本章多个小节

    Args:
        payload: 包含 multiple_choice 和 fill_in_blank 的完整 JSON 数据

    Returns:
        过滤后的数据（原地修改并返回）
    """
    mc: List[Dict[str, Any]] = payload.get("multiple_choice") or []
    fb: List[Dict[str, Any]] = payload.get("fill_in_blank") or []

    filtered_mc = [q for q in mc if not is_bad_referenced_question(q)]
    filtered_fb = [q for q in fb if not is_bad_referenced_question(q)]

    removed_mc = len(mc) - len(filtered_mc)
    removed_fb = len(fb) - len(filtered_fb)

    if removed_mc or removed_fb:
        print(
            f"[filter] 移除了 {removed_mc} 道选择题、{removed_fb} 道填空题（含算法/例/图/表编号）。"
        )

    payload["multiple_choice"] = filtered_mc
    payload["fill_in_blank"] = filtered_fb

    # 检查过滤后题目数量
    if len(filtered_mc) < MIN_QUESTIONS_PER_TYPE:
        print(
            f"[警告] 选择题数量少于 {MIN_QUESTIONS_PER_TYPE} 道（当前 {len(filtered_mc)} 道），可能是过滤掉过多编号题导致的。"
        )
    if len(filtered_fb) < MIN_QUESTIONS_PER_TYPE:
        print(
            f"[警告] 填空题数量少于 {MIN_QUESTIONS_PER_TYPE} 道（当前 {len(filtered_fb)} 道），可能是过滤掉过多编号题导致的。"
        )

    return payload


def supplement_questions(
    chapter_text: str,
    chapter_id: Optional[int],
    chapter_title: Optional[str],
    existing_questions: Dict[str, Any],
    api_key: str,
    model: str,
    temperature: float = 0.4,
) -> Dict[str, Any]:
    """
    当题目数量不足时，补充生成题目。

    Args:
        chapter_text: 章节文本
        chapter_id: 章节编号
        chapter_title: 章节标题
        existing_questions: 已生成的题目（用于去重）
        api_key: API 密钥
        model: 模型名称
        temperature: 采样温度

    Returns:
        补充的题目数据（只包含 multiple_choice 和 fill_in_blank）
    """
    mc_count = len(existing_questions.get("multiple_choice", []))
    fb_count = len(existing_questions.get("fill_in_blank", []))

    need_mc = max(0, MIN_QUESTIONS_PER_TYPE - mc_count)
    need_fb = max(0, MIN_QUESTIONS_PER_TYPE - fb_count)

    if need_mc == 0 and need_fb == 0:
        return {"multiple_choice": [], "fill_in_blank": []}

    print(f"[补题] 需要补充 {need_mc} 道选择题、{need_fb} 道填空题。")

    # 构建补充出题的 prompt
    supplement_prompt = build_prompt(
        chapter_text, chapter_id, chapter_title, is_supplement=True
    )
    # 修改 prompt 中的题目数量要求
    supplement_prompt = supplement_prompt.replace(
        "2. 5 道单选题（multiple_choice）\n3. 5 道填空题（fill_in_blank）",
        f"2. {need_mc} 道单选题（multiple_choice）\n3. {need_fb} 道填空题（fill_in_blank）",
    )

    raw_content = call_deepseek(api_key, model, supplement_prompt, temperature)
    supplement_data = parse_json_only(raw_content)
    # 对补充的题目也进行过滤
    supplement_data = filter_questions(supplement_data)

    # 合并题目（保留原有的 meta）
    existing_mc = existing_questions.get("multiple_choice", [])
    existing_fb = existing_questions.get("fill_in_blank", [])

    new_mc = supplement_data.get("multiple_choice", [])
    new_fb = supplement_data.get("fill_in_blank", [])

    # 重新编号，确保 ID 连续
    max_mc_id = max([q.get("id", 0) for q in existing_mc], default=0)
    max_fb_id = max([q.get("id", 0) for q in existing_fb], default=0)

    for idx, q in enumerate(new_mc):
        q["id"] = max_mc_id + idx + 1
    for idx, q in enumerate(new_fb):
        q["id"] = max_fb_id + idx + 1

    return {
        "multiple_choice": new_mc,
        "fill_in_blank": new_fb,
    }


def parse_json_only(raw_content: str) -> Dict[str, Any]:
    """
    仅解析 JSON，不进行过滤和校验（用于内部调用）。
    """
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "").replace("JSON\n", "")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"解析 JSON 失败，请手动检查模型输出。\n错误：{e}\n原始内容：\n{text}"
        ) from e


def parse_questions_json(raw_content: str) -> Dict[str, Any]:
    """
    尝试把模型输出解析成 JSON。
    如果解析失败，则抛出异常，方便你手动检查原始输出。
    兼容 meta 字段，如果缺失则只打印警告。
    """
    data = parse_json_only(raw_content)

    # 结构校验
    if "multiple_choice" not in data or "fill_in_blank" not in data:
        print("警告：JSON 中缺少 multiple_choice 或 fill_in_blank 字段。")

    # 检查 meta 字段
    if "meta" not in data:
        print("警告：JSON 中缺少 meta 字段，后续渲染脚本可能无法自动生成标题和描述。")
    else:
        meta = data.get("meta", {})
        required_meta_fields = ["chapter_index", "chapter_title", "quiz_title", "quiz_description"]
        missing_fields = [f for f in required_meta_fields if f not in meta]
        if missing_fields:
            print(f"警告：meta 中缺少以下字段：{', '.join(missing_fields)}")

    # 过滤掉包含算法/例题/图表编号的题目
    data = filter_questions(data)

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
        default=None,
        help="DeepSeek API Key（可通过参数、环境变量或脚本内默认值提供）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.4,
        help="采样温度，默认为 0.4（偏稳重一点）",
    )
    parser.add_argument(
        "--chapter-id",
        type=int,
        default=None,
        help="章节编号（可选，用于提示模型，例如 2）",
    )
    parser.add_argument(
        "--chapter-title",
        type=str,
        default=None,
        help="章节标题（可选，用于提示模型，例如 '第2章 线性表'）",
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
    prompt = build_prompt(
        chapter_text,
        chapter_id=args.chapter_id,
        chapter_title=args.chapter_title,
    )
    raw_content = call_deepseek(
        api_key=api_key,
        model=args.model,
        prompt=prompt,
        temperature=args.temperature,
    )
    questions = parse_questions_json(raw_content)

    # 检查题目数量，如果不足则补充
    mc_count = len(questions.get("multiple_choice", []))
    fb_count = len(questions.get("fill_in_blank", []))

    if mc_count < MIN_QUESTIONS_PER_TYPE or fb_count < MIN_QUESTIONS_PER_TYPE:
        print(f"[补题] 检测到题目数量不足，开始补充生成...")
        supplement = supplement_questions(
            chapter_text=chapter_text,
            chapter_id=args.chapter_id,
            chapter_title=args.chapter_title,
            existing_questions=questions,
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
        )

        # 合并补充的题目
        questions["multiple_choice"].extend(supplement.get("multiple_choice", []))
        questions["fill_in_blank"].extend(supplement.get("fill_in_blank", []))

        print(
            f"[补题] 补充完成，当前有 {len(questions['multiple_choice'])} 道选择题、"
            f"{len(questions['fill_in_blank'])} 道填空题。"
        )

    save_output_json(questions, output_path)


if __name__ == "__main__":
    main()
