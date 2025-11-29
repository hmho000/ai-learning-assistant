import fitz  # PyMuPDF
import re
import json
import requests
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import Chapter, Quiz, Question
from sqlmodel import Session

# === Constants ===
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# === PDF Parsing Service ===

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    简单提取 PDF 全文文本
    """
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_chapters_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    尝试从 PDF 目录提取章节
    返回: [{"title": "第1章...", "content": "..."}]
    """
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    chapters = []
    
    # 如果没有目录，这就比较麻烦，暂时只做一个简单的全书作为一个章节
    if not toc:
        full_text = extract_text_from_pdf(pdf_path)
        chapters.append({
            "title": "全书内容",
            "index": 1,
            "content": full_text
        })
        return chapters

    # 简单的目录解析逻辑
    # 寻找一级目录
    level1_nodes = [item for item in toc if item[0] == 1]
    
    for i, node in enumerate(level1_nodes):
        title = node[1]
        start_page = node[2]
        
        # 确定结束页码
        if i < len(level1_nodes) - 1:
            end_page = level1_nodes[i+1][2]
        else:
            end_page = doc.page_count
            
        # 提取该范围的文本
        chapter_text = ""
        # fitz 页码从 0 开始，toc 从 1 开始
        for p in range(start_page - 1, end_page - 1):
            if p < doc.page_count:
                chapter_text += doc[p].get_text()
        
        chapters.append({
            "title": title,
            "index": i + 1,
            "content": chapter_text
        })
        
    return chapters


def generate_quiz_for_chapter(chapter_text: str, chapter_title: str, num_mc: int = 5, num_fb: int = 5) -> Dict[str, Any]:
    """
    调用 DeepSeek 生成题目
    """
    # 优先从环境变量获取，如果没有则报错
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in environment variables.")
        # Return empty structure to avoid crashing
        return {"multiple_choice": [], "fill_in_blank": []}
    
    prompt = f"""
你是一名专业的教育测评专家。
请阅读以下章节内容（标题：{chapter_title}），并生成 {num_mc} 道单选题和 {num_fb} 道填空题。

要求：
1. 题目必须基于提供的文本。
2. 输出必须是合法的 JSON 格式。
3. 不要包含 markdown 标记。

JSON 结构示例：
{{
  "quiz_title": "...",
  "quiz_description": "...",
  "multiple_choice": [
    {{ "question": "...", "options": ["A...", "B...", "C...", "D..."], "answer": "A", "explanation": "..." }}
  ],
  "fill_in_blank": [
    {{ "question": "...", "answer": "...", "explanation": "..." }}
  ]
}}

【章节内容开始】
{chapter_text[:8000]} 
【章节内容结束】
(注：内容已截断，仅供参考)
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个辅助出题的 AI 助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "stream": False,
    }
    
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        # 清理 markdown 标记
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        
        return json.loads(content)
    except Exception as e:
        print(f"AI Generation Error: {e}")
        # 返回空数据避免 crash
        return {"multiple_choice": [], "fill_in_blank": []}

def save_quiz_to_db(session: Session, chapter_id: int, quiz_data: Dict[str, Any]):
    """
    将生成的 JSON 数据保存到数据库
    """
    quiz = Quiz(
        chapter_id=chapter_id,
        title=quiz_data.get("quiz_title", "自动生成的练习"),
        description=quiz_data.get("quiz_description", "AI 智能生成")
    )
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    
    # 保存选择题
    for q in quiz_data.get("multiple_choice", []):
        question = Question(
            quiz_id=quiz.id,
            type="multiple_choice",
            stem=q["question"],
            options_json=json.dumps(q["options"], ensure_ascii=False),
            answer=q["answer"],
            explanation=q.get("explanation")
        )
        session.add(question)
        
    # 保存填空题
    for q in quiz_data.get("fill_in_blank", []):
        question = Question(
            quiz_id=quiz.id,
            type="fill_in_blank",
            stem=q["question"],
            answer=q["answer"],
            explanation=q.get("explanation")
        )
        session.add(question)
        
    session.commit()
    return quiz
