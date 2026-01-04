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
    # Ensure env is loaded
    # 优先从环境变量获取，如果没有则报错
    # Ensure env is loaded
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key.strip() == "sk-your_api_key_here":
        raise ValueError("未配置有效的 DEEPSEEK_API_KEY，请检查 .env 文件。")
    
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
        print(f"Sending request to DeepSeek API for chapter: {chapter_title}...")
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        # 清理 markdown 标记
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        
        return json.loads(content)
    except requests.exceptions.Timeout:
        raise RuntimeError("DeepSeek API 请求超时，请稍后重试。")
    except requests.exceptions.RequestException as e:
        error_msg = f"DeepSeek API 调用失败: {e}"
        if e.response is not None:
             error_msg += f" (Status: {e.response.status_code})"
        raise RuntimeError(error_msg)
    except Exception as e:
        raise RuntimeError(f"题目生成发生错误: {e}")

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

def export_quiz_to_word(quiz_data: Dict[str, Any], output_path: str, include_answers: bool = True):
    """
    将题目数据导出为 Word 文档
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
    except ImportError:
        print("Error: python-docx not installed.")
        return False

    doc = Document()
    
    # 设置全文档默认字体为宋体
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman' # 西文
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体') # 中文
    
    # 标题
    title = quiz_data.get("title", "练习题")
    heading = doc.add_heading(title, 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # 标题也设置一下字体，虽然 Heading 样式可能不同，但为了保险
    for run in heading.runs:
        run.font.name = 'Times New Roman'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 描述
    if quiz_data.get("description"):
        p = doc.add_paragraph(quiz_data["description"])
    
    doc.add_paragraph("-" * 50)

    questions = quiz_data.get("questions", [])
    
    # 分类题目
    mc_questions = [q for q in questions if q["type"] == "multiple_choice"]
    fb_questions = [q for q in questions if q["type"] == "fill_in_blank"]
    
    # 1. 单选题
    if mc_questions:
        doc.add_heading("一、单选题", level=1)
        for i, q in enumerate(mc_questions, 1):
            # 题干
            p = doc.add_paragraph()
            run = p.add_run(f"{i}. {q['stem']}")
            run.font.size = Pt(12)
            
            # 选项
            if q.get("options_json"):
                try:
                    options = json.loads(q["options_json"])
                    for opt in options:
                        doc.add_paragraph(f"   {opt}")
                except:
                    pass
            
            # 答案和解析
            if include_answers:
                ans_p = doc.add_paragraph()
                ans_run = ans_p.add_run(f"【答案】 {q.get('answer')}")
                ans_run.font.bold = True
                ans_run.font.color.rgb = RGBColor(0, 100, 0)  # Dark Green
                
                if q.get("explanation"):
                    exp_p = doc.add_paragraph()
                    exp_run = exp_p.add_run(f"【解析】 {q['explanation']}")
                    exp_run.font.italic = True
                    exp_run.font.color.rgb = RGBColor(100, 100, 100) # Gray
            
            doc.add_paragraph() # Spacer

    # 2. 填空题
    if fb_questions:
        doc.add_heading("二、填空题", level=1)
        for i, q in enumerate(fb_questions, 1):
            # 题干
            p = doc.add_paragraph()
            run = p.add_run(f"{i}. {q['stem']}")
            run.font.size = Pt(12)
            
            # 这里的填空题通常是在题干里挖空，或者直接问
            # 如果是挖空，通常不需要额外展示什么，用户直接在横线上写
            # 但为了 Word 导出好看，可以加个下划线占位如果题干里没有的话
            # 这里简单处理，直接展示题干
            
            # 答案和解析
            if include_answers:
                ans_p = doc.add_paragraph()
                ans_run = ans_p.add_run(f"【答案】 {q.get('answer')}")
                ans_run.font.bold = True
                ans_run.font.color.rgb = RGBColor(0, 100, 0)
                
                if q.get("explanation"):
                    exp_p = doc.add_paragraph()
                    exp_run = exp_p.add_run(f"【解析】 {q['explanation']}")
                    exp_run.font.italic = True
                    exp_run.font.color.rgb = RGBColor(100, 100, 100)
            
            doc.add_paragraph() # Spacer
            
    try:
        doc.save(output_path)
        return True
    except Exception as e:
        print(f"Error saving word document: {e}")
        return False
