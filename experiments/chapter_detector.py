"""
chapter_detector.py
-------------------

自动章节识别：
- 支持中文“第X章 / 第一章 / 1.2” 等格式
- 支持英文 “Chapter 2 / Part III / 2.3 Data Model” 等格式
- 若无法识别章节，退化为“全文”单章节
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Pattern


MIN_SEGMENT_LENGTH = 200


@dataclass
class HeadingPattern:
    pattern: Pattern[str]
    weight: float


HEADING_PATTERNS: List[HeadingPattern] = [
    HeadingPattern(
        re.compile(r"^第\s*[一二三四五六七八九十百零\d]+\s*(章|节|篇|部分|卷)\b.*"), 3.0
    ),
    HeadingPattern(
        re.compile(r"^[一二三四五六七八九十百零]+\s*[、.]\s*.+"), 2.0
    ),
    HeadingPattern(
        re.compile(r"^\d+(\.\d+){0,2}\s+.+"), 2.5
    ),
    HeadingPattern(
        re.compile(r"^(Chapter|CHAPTER|Part|PART|Section|SECTION)\s+[0-9IVXLC]+\b.*"), 3.0
    ),
    HeadingPattern(
        re.compile(r"^[A-Z][A-Za-z]+\s+\d+(\.\d+)?\b.*"), 1.5
    ),
]


def split_into_chapters(full_text: str) -> List[Dict]:
    """
    返回章节列表：
    [
      { "id": 1, "title": "Chapter 1 Introduction", "text": "..." },
      ...
    ]
    """
    full_text = (full_text or "").strip()
    if not full_text:
        return [{"id": 1, "title": "全文", "text": ""}]

    candidates = _collect_heading_candidates(full_text)
    if not candidates:
        return [{"id": 1, "title": "全文", "text": full_text}]

    chapters: List[Dict] = []
    text_length = len(full_text)

    for idx, candidate in enumerate(candidates):
        start = candidate["start"]
        end = candidates[idx + 1]["start"] if idx + 1 < len(candidates) else text_length
        segment = full_text[start:end].strip()
        if not segment:
            continue

        segment_length = len(segment)
        score = candidate["score"] + segment_length / 1000

        if segment_length < MIN_SEGMENT_LENGTH and len(candidates) > 1:
            continue

        chapters.append(
            {
                "id": len(chapters) + 1,
                "title": candidate["title"],
                "text": segment,
                "score": score,
            }
        )

    if not chapters:
        return [{"id": 1, "title": "全文", "text": full_text}]

    chapters.sort(key=lambda item: item["id"])
    for ch in chapters:
        ch.pop("score", None)
    return chapters


def _collect_heading_candidates(full_text: str) -> List[Dict]:
    lines = full_text.splitlines()
    candidates: List[Dict] = []
    cursor = 0

    for line in lines:
        stripped = line.strip()
        line_length = len(line)
        if not stripped or len(stripped) > 160:
            cursor += line_length + 1
            continue

        matched = _match_heading(stripped)
        if matched:
            title = stripped
            score = matched.weight
            if candidates and cursor - candidates[-1]["start"] < 120:
                cursor += line_length + 1
                continue
            candidates.append({"start": cursor, "title": title, "score": score})

        cursor += line_length + 1

    return candidates


def _match_heading(line: str):
    for heading in HEADING_PATTERNS:
        if heading.pattern.match(line):
            return heading
    return None


if __name__ == "__main__":  # 简单测试
    sample = """第1章 绪论
内容A
第2章 线性表
内容B"""
    for ch in split_into_chapters(sample):
        print(ch["id"], ch["title"], len(ch["text"]))

