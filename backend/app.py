"""
FastAPI 后端应用：
1. 提供 /api/* 接口（后续可接入真正的出题逻辑）
2. 托管打包后的 React + Vite 前端（frontend/dist）

说明：
- 开发模式（直接用 Python 运行）时，前端构建输出目录约定为项目根目录下的 frontend/dist。
- 打包模式（run_app.exe，PyInstaller 单文件）时，构建脚本会将 frontend/dist 复制到 exe 同级目录的 frontend/dist，
  本文件会优先从 exe 所在目录查找该路径。
如果未来调整了前端目录结构，请同步更新 FRONTEND_DIST_DIR 的路径逻辑。
"""

import os
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Course, Chapter, Quiz, Question, QuizReadWithQuestions, ChapterRead, MistakeRecord
from .models import Course, Chapter, Quiz, Question, QuizReadWithQuestions, ChapterRead, MistakeRecord
from .services import parse_chapters_from_file, generate_quiz_for_chapter, save_quiz_to_db
import shutil
from pathlib import Path
from datetime import datetime

# === 创建 FastAPI 实例 ===
app = FastAPI(title="AI 学习助手 Backend")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# === 静态文件 & 前端托管 ===
# 优先从打包后 exe 所在目录查找 frontend/dist（适用于 PyInstaller 单文件）；
# 如果不是打包运行，则退回到源码目录结构（项目根目录 /frontend/dist）。
def resolve_frontend_dist_dir() -> str:
    # 情况 1：PyInstaller 打包后的单文件（sys.frozen 为 True）
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidate = os.path.join(exe_dir, "frontend", "dist")
        if os.path.isdir(candidate):
            return candidate

    # 情况 2：普通 Python 运行，使用源码目录结构
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
    )


FRONTEND_DIST_DIR = resolve_frontend_dist_dir()

# 打印调试信息（在打包后的 exe 中也能看到）
print(f"[INFO] Frontend dist directory: {FRONTEND_DIST_DIR}")
print(f"[INFO] Directory exists: {os.path.isdir(FRONTEND_DIST_DIR)}")

if not os.path.isdir(FRONTEND_DIST_DIR):
    # 如果目录不存在，不要让应用崩掉，只提示一下
    print(
        f"[WARN] Frontend dist directory not found: {FRONTEND_DIST_DIR}. "
        f"Please run `npm run build` (or `pnpm build` / `yarn build`) in frontend/ first."
    )

# 挂载静态资源，例如 /assets/*
# 注意：mount 必须在路由之前，FastAPI 会按顺序匹配
assets_dir = os.path.join(FRONTEND_DIST_DIR, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    print(f"[INFO] Mounted /assets from: {assets_dir}")
else:
    print(f"[WARN] Assets directory not found: {assets_dir}")

# 挂载 questions 目录（包含 manifest.json 和题库文件）
# 必须在通配路由之前挂载，否则会被拦截
questions_dir = os.path.join(FRONTEND_DIST_DIR, "questions")
if os.path.isdir(questions_dir):
    app.mount("/questions", StaticFiles(directory=questions_dir), name="questions")
    print(f"[INFO] Mounted /questions from: {questions_dir}")
    # 列出 questions 目录中的文件，方便调试
    try:
        files = os.listdir(questions_dir)
        print(f"[INFO] Questions directory contains: {', '.join(files[:10])}")  # 只显示前10个
    except Exception as e:
        print(f"[WARN] Cannot list questions directory: {e}")
else:
    print(f"[WARN] Questions directory not found: {questions_dir}")

# 添加一个中间件来禁用 questions 目录的缓存
@app.middleware("http")
async def no_cache_questions(request, call_next):
    response = await call_next(request)
    # 如果是 questions 目录的请求，禁用缓存
    if request.url.path.startswith("/questions/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def index_html_path() -> str:
    return os.path.join(FRONTEND_DIST_DIR, "index.html")


# === API 接口（必须在通配路由之前注册） ===
@app.get("/api/health")
async def api_health():
    return {"status": "ok"}

@app.post("/api/upload")
def upload_file(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    上传文件，创建 Course 记录
    支持 PDF 和 图片 (png, jpg, jpeg)
    """
    allowed_exts = {".pdf", ".png", ".jpg", ".jpeg"}
    ext = Path(file.filename).suffix.lower()
    
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only PDF and Image files (.png, .jpg, .jpeg) are allowed")
    
    # 保存文件到 data 目录
    upload_dir = Path("data")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    
    # 使用 shutil.copyfileobj 高效写入
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 创建数据库记录
    # 简单起见，用文件名作为课程标题
    course_title = file.filename.rsplit(".", 1)[0]
    course = Course(title=course_title, description="Uploaded via Web")
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return {"status": "success", "course_id": course.id, "filename": file.filename}

# === 题型排序常量 ===
# 定义题型的显示顺序
QUESTION_TYPE_ORDER = {
    "multiple_choice": 1,      # 单选题
    "multi_select": 2,          # 多选题
    "fill_in_blank": 3,         # 填空题
    "true_false": 4,            # 判断题
    "short_answer": 5,          # 简答题
    "code": 6,                  # 代码题
}

# === 错题本 API ===

# 1. 添加错题 (当用户答错时调用)
@app.post("/api/mistakes")
def add_mistake(record: MistakeRecord, session: Session = Depends(get_session)):
    # 防止重复添加：检查同一课程下的同一道题是否已经在错题本里了
    existing = session.exec(
        select(MistakeRecord).where(
            MistakeRecord.question_id == record.question_id,
            MistakeRecord.course_id == record.course_id
        )
    ).first()
    if existing:
        # 如果已经存在，更新时间即可
        existing.created_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"status": "updated", "message": "Mistake record updated"}
    
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

# 2. 获取某课程的所有错题 (包含题目详情，按题型排序)
@app.get("/api/courses/{course_id}/mistakes")
def get_course_mistakes(course_id: int, session: Session = Depends(get_session)):
    """
    获取课程的所有错题，按题型顺序返回
    返回格式：按单选 → 多选 → 填空 → 判断 → 简答 → 代码 排序
    
    重要：题号是相对于每个 quiz 的，不是全局 ID
    - question.id 是数据库全局 ID（用于删除等操作）
    - question_number 是相对于该 quiz 的题号（1-5）
    """
    # 这是一个联表查询：从 MistakeRecord 查，同时把对应的 Question 数据抓出来
    statement = select(Question, MistakeRecord).join(
        MistakeRecord, Question.id == MistakeRecord.question_id
    ).where(MistakeRecord.course_id == course_id)
    results = session.exec(statement).all()
    
    # 组装返回数据，计算相对题号
    mistakes = []
    for question, record in results:
        # 计算该题在其所属 quiz 中、同一类型内的相对位置
        same_type_questions = session.exec(
            select(Question)
            .where(
                Question.quiz_id == question.quiz_id,
                Question.type == question.type
            )
            .order_by(Question.id)
        ).all()
        
        # 找出该题在同类型题中的相对位置
        relative_number = 1
        for idx, q in enumerate(same_type_questions, 1):
            if q.id == question.id:
                relative_number = idx
                break
        
        # 将题目信息和错题记录时间组合返回
        q_dict = question.model_dump()
        q_dict["mistake_date"] = record.created_at.isoformat() if hasattr(record.created_at, 'isoformat') else str(record.created_at)
        q_dict["question_number"] = relative_number  # 添加相对题号
        mistakes.append(q_dict)
    
    # 按题型优先级、再按相对题号排序
    def sort_key(item):
        type_order = QUESTION_TYPE_ORDER.get(item["type"], 999)
        question_number = item.get("question_number", 999)
        return (type_order, question_number)
    
    mistakes.sort(key=sort_key)
    return mistakes

# 3. 移除错题 (修复：加入 course_id 参数确保只删除指定课程的错题)
@app.delete("/api/courses/{course_id}/mistakes/{question_id}")
def remove_mistake(course_id: int, question_id: int, session: Session = Depends(get_session)):
    """
    移除指定课程的错题
    参数:
        course_id: 课程ID
        question_id: 题目ID
    """
    # 精确删除：确保只删除指定课程下的该题目
    statement = select(MistakeRecord).where(
        MistakeRecord.question_id == question_id,
        MistakeRecord.course_id == course_id
    )
    results = session.exec(statement).all()
    for mistake in results:
        session.delete(mistake)
    session.commit()
    return {"status": "success", "message": "Removed from mistake book"}


@app.get("/api/courses", response_model=list[Course])
async def get_courses(session: Session = Depends(get_session)):
    courses = session.exec(select(Course)).all()
    return courses

def process_course_generation(course_id: int, filename: str, session: Session):
    """
    后台任务：解析 PDF -> 生成题目 -> 存入数据库
    """
    try:
        print(f"[Task] Starting generation for course {course_id} ({filename})")
        pdf_path = Path("data") / filename
        
        # 1. 解析章节
        chapters_data = parse_chapters_from_file(str(pdf_path))
        print(f"[Task] Parsed {len(chapters_data)} chapters")
        
        for ch_data in chapters_data:
            # 保存章节
            chapter = Chapter(
                course_id=course_id,
                title=ch_data["title"],
                index=ch_data["index"],
                content_text=ch_data["content"]
            )
            session.add(chapter)
            session.commit()
            session.refresh(chapter)
            
            # 2. 生成题目
            print(f"[Task] Generating quiz for chapter: {chapter.title}")
            quiz_data = generate_quiz_for_chapter(chapter.content_text, chapter.title)
            
            if quiz_data:
                # 3. 保存题目
                save_quiz_to_db(session, chapter.id, quiz_data)
                print(f"[Task] Saved quiz for chapter: {chapter.title}")
            else:
                print(f"[Task] Failed to generate quiz for chapter: {chapter.title}")
            
        # 更新课程状态
        course = session.get(Course, course_id)
        if course:
            course.status = "ready"
            session.add(course)
            session.commit()
            
        print(f"[Task] Completed generation for course {course_id}")

    except Exception as e:
        print(f"[Task] Error generating course {course_id}: {e}")
        try:
            course = session.get(Course, course_id)
            if course:
                course.status = "error"
                session.add(course)
                session.commit()
        except Exception as db_e:
            print(f"[Task] Failed to update error status: {db_e}")

def process_course_parsing(course_id: int, filename: str, session: Session):
    """
    后台任务：解析 PDF -> 存入章节 -> 状态改为 parsed
    """
    try:
        print(f"[Task] Starting parsing for course {course_id} ({filename})")
        pdf_path = Path("data") / filename
        
        # 1. 解析章节
        chapters_data = parse_chapters_from_file(str(pdf_path))
        print(f"[Task] Parsed {len(chapters_data)} chapters")
        
        for ch_data in chapters_data:
            # 保存章节
            chapter = Chapter(
                course_id=course_id,
                title=ch_data["title"],
                index=ch_data["index"],
                content_text=ch_data["content"]
            )
            session.add(chapter)
        
        # 更新课程状态
        course = session.get(Course, course_id)
        if course:
            course.status = "parsed"
            session.add(course)
        
        session.commit()
        print(f"[Task] Completed parsing for course {course_id}")

    except Exception as e:
        print(f"[Task] Error parsing course {course_id}: {e}")
        try:
            course = session.get(Course, course_id)
            if course:
                course.status = "error"
                session.add(course)
                session.commit()
        except Exception as db_e:
            print(f"[Task] Failed to update error status: {db_e}")

def process_course_generation_custom(course_id: int, config: dict, session: Session):
    """
    后台任务：根据配置生成题目
    config: { chapter_ids: [1, 2], num_mc: 5, num_fb: 5 }
    """
    try:
        print(f"[Task] Starting custom generation for course {course_id} with config {config}")
        
        # 获取章节
        statement = select(Chapter).where(Chapter.course_id == course_id)
        if config.get("chapter_ids"):
             statement = statement.where(Chapter.id.in_(config["chapter_ids"]))
        
        chapters = session.exec(statement).all()
        total_chapters = len(chapters)
        print(f"[Task] Generating for {total_chapters} chapters")
        
        # 初始化进度
        course = session.get(Course, course_id)
        if course:
            course.generation_total_chapters = total_chapters
            course.generation_current_chapter = 0
            course.generation_status_message = "准备开始生成..."
            session.add(course)
            session.commit()

        for i, chapter in enumerate(chapters):
             # 更新章节开始进度
            course = session.get(Course, course_id)
            if course:
                course.generation_current_chapter = i
                course.generation_status_message = f"正在生成第 {i+1}/{total_chapters} 章: {chapter.title}"
                session.add(course)
                session.commit()

             # 2. 生成题目
            print(f"[Task] Generating quiz for chapter: {chapter.title}")
            quiz_data = generate_quiz_for_chapter(
                chapter.content_text, 
                chapter.title,
                num_mc=config.get("num_mc", 5),
                num_multi=config.get("num_multi", 0),
                num_tf=config.get("num_tf", 0),
                num_fb=config.get("num_fb", 5),
                num_short=config.get("num_short", 0),
                num_code=config.get("num_code", 0),
                difficulty=config.get("difficulty", "medium")
            )
            
            if quiz_data:
                # 3. 保存题目
                save_quiz_to_db(session, chapter.id, quiz_data)
                print(f"[Task] Saved quiz for chapter: {chapter.title}")
            else:
                print(f"[Task] Failed to generate quiz for chapter: {chapter.title} (Empty response)")
                # 更新状态消息以反映错误
                course = session.get(Course, course_id)
                if course:
                    course.generation_status_message = f"生成失败: {chapter.title}"
                    session.add(course)
                    session.commit()
            
        # 最终更新
        course = session.get(Course, course_id)
        if course:
            course.generation_current_chapter = total_chapters
            course.generation_status_message = "生成完成！"
            session.add(course)
            session.commit()

        # 更新课程状态
        course = session.get(Course, course_id)
        if course:
            course.status = "ready"
            session.add(course)
            session.commit()
            
        print(f"[Task] Completed generation for course {course_id}")

    except Exception as e:
        print(f"[Task] Error generating course {course_id}: {e}")
        try:
            course = session.get(Course, course_id)
            if course:
                course.status = "error"
                course.generation_status_message = f"生成出错: {str(e)}"
                session.add(course)
                session.commit()
        except Exception as db_e:
            print(f"[Task] Failed to update error status: {db_e}")


@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # 删除相关文件（可选，但建议这样做）
    # 假设我们存储了文件名或可以推导出它。
    # 当前模型除了标题外没有明确存储文件名。
    # 暂时跳过文件删除，以免误删。
    
    session.delete(course)
    session.commit()
    
    return {"status": "success", "message": "Course deleted successfully"}

def run_generation_task(course_id: int, filename: str):
    """
    为后台任务创建新会话的包装器
    """
    from .database import engine
    with Session(engine) as session:
        process_course_generation(course_id, filename, session)

def run_parsing_task(course_id: int, filename: str):
    from .database import engine
    with Session(engine) as session:
        process_course_parsing(course_id, filename, session)

def run_custom_generation_task(course_id: int, config: dict):
    from .database import engine
    with Session(engine) as session:
        process_course_generation_custom(course_id, config, session)

@app.post("/api/courses/{course_id}/parse")
async def parse_course_endpoint(course_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # 查找对应的文件（支持多种扩展名）
    data_dir = Path("data")
    filename = None
    # 优先精确匹配（如果逻辑严谨的话应该不会有重名不同后缀），这里简单遍历
    for ext in [".pdf", ".png", ".jpg", ".jpeg"]:
        candidate = f"{course.title}{ext}"
        if (data_dir / candidate).exists():
            filename = candidate
            break
            
    if not filename:
         # 尝试一种更宽容的搜索（如果是旧数据可能标题和文件名不一致？）
         # 也可以尝试 listdir 匹配 startswith
         raise HTTPException(status_code=404, detail=f"Source file for course '{course.title}' not found in data directory.")
    
    print(f"[INFO] Found source file for parsing: {filename}")
    
    course.status = "parsing"
    session.add(course)
    session.commit()
    
    background_tasks.add_task(run_parsing_task, course_id, filename)
    return {"status": "accepted", "message": "Parsing task started"}

@app.post("/api/courses/{course_id}/generate")
async def generate_course_endpoint(course_id: int, config: dict, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # 检查 API 密钥
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key.strip() == "sk-your_api_key_here":
        print(f"[ERROR] Invalid API Key. Tried loading from: {env_path.resolve()}")
        raise HTTPException(status_code=400, detail="未配置有效的 DEEPSEEK_API_KEY，请检查 .env 文件。")
    
    course.status = "generating"
    session.add(course)
    session.commit()
    
    background_tasks.add_task(run_custom_generation_task, course_id, config)
    return {"status": "accepted", "message": "Generation task started"}

@app.get("/api/courses/{course_id}/chapters", response_model=list[ChapterRead])
async def get_course_chapters(course_id: int, session: Session = Depends(get_session)):
    # 使用 selectinload 高效获取测验
    from sqlalchemy.orm import selectinload
    statement = select(Chapter).where(Chapter.course_id == course_id).options(selectinload(Chapter.quizzes))
    chapters = session.exec(statement).all()
    
    result = []
    for ch in chapters:
        has_quiz = len(ch.quizzes) > 0
        result.append(ChapterRead(
            id=ch.id,
            title=ch.title,
            index=ch.index,
            has_quiz=has_quiz
        ))
    return result

@app.get("/api/chapters/{chapter_id}/quiz", response_model=list[QuizReadWithQuestions])
async def get_chapter_quiz(chapter_id: int, session: Session = Depends(get_session)):
    quizzes = session.exec(select(Quiz).where(Quiz.chapter_id == chapter_id)).all()
    return quizzes

@app.get("/api/chapters/{chapter_id}/export-word")
async def export_chapter_quiz_word(chapter_id: int, include_answers: bool = True, session: Session = Depends(get_session)):
    """
    导出章节题目为 Word 文档
    """
    # 1. 获取题目数据
    # 这里我们复用获取题目的逻辑，或者直接查库
    # 为了方便，我们先查 Quiz，再查 Questions
    # 注意：一个章节可能有多个 Quiz，这里我们默认导出第一个，或者合并所有
    # 简单起见，导出该章节下的所有 Quiz
    
    quizzes = session.exec(select(Quiz).where(Quiz.chapter_id == chapter_id)).all()
    if not quizzes:
        raise HTTPException(status_code=404, detail="No quizzes found for this chapter")
    
    # 构造导出数据
    # 如果有多个 quiz，我们合并它们
    chapter = session.get(Chapter, chapter_id)
    chapter_title = chapter.title if chapter else f"Chapter {chapter_id}"
    
    all_questions = []
    for quiz in quizzes:
        # 加载 questions
        # 注意：这里需要确保 questions 已经被加载
        # 如果是 lazy load，可能需要显式查询
        questions = session.exec(select(Question).where(Question.quiz_id == quiz.id)).all()
        for q in questions:
            all_questions.append({
                "type": q.type,
                "stem": q.stem,
                "options_json": q.options_json,
                "answer": q.answer,
                "explanation": q.explanation
            })
            
    export_data = {
        "title": f"{chapter_title} - 练习题",
        "description": f"共 {len(all_questions)} 道题",
        "questions": all_questions
    }
    
    # 2. 生成 Word 文件
    from .services import export_quiz_to_word
    import tempfile
    
    # 创建临时文件
    temp_dir = tempfile.gettempdir()
    
    # 优化文件名：章节名_教师版/学生版.docx
    suffix = "教师版" if include_answers else "学生版"
    # 清理文件名中的非法字符
    safe_title = "".join([c for c in chapter_title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
    filename = f"{safe_title}_{suffix}.docx"
    
    file_path = os.path.join(temp_dir, filename)
    
    success = export_quiz_to_word(export_data, file_path, include_answers=include_answers)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate Word document")
        
    # 3. 返回文件
    return FileResponse(
        path=file_path, 
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

from pydantic import BaseModel

class GradeShortAnswerRequest(BaseModel):
    question_id: int
    answer: str

class ReviewCodeRequest(BaseModel):
    question_id: int
    code: str

@app.post("/api/grade/short-answer")
def api_grade_short_answer(req: GradeShortAnswerRequest, session: Session = Depends(get_session)):
    from .services import grade_short_answer
    question = session.get(Question, req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 使用题干和参考答案进行评分
    result = grade_short_answer(question.stem, question.answer, req.answer)
    return result

@app.post("/api/grade/code")
def api_review_code(req: ReviewCodeRequest, session: Session = Depends(get_session)):
    from .services import review_code
    question = session.get(Question, req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    result = review_code(question.stem, question.answer, req.code)
    return result

@app.get("/api/debug/manifest")
async def debug_manifest():
    """调试接口：返回 manifest.json 的内容"""
    import json
    manifest_path = os.path.join(FRONTEND_DIST_DIR, "questions", "manifest.json")
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "status": "ok",
            "path": manifest_path,
            "exists": True,
            "data": data,
            "courses_count": len(data.get("courses", []))
        }
    return {
        "status": "error",
        "path": manifest_path,
        "exists": False
    }

@app.get("/api/sample-quiz")
async def api_sample_quiz():
    """
    示例题目数据（前端可以先用这个接口打通联调），后续替换为真实数据。
    """
    return {
        "chapterTitle": "第 1 章 绪论（示例）",
        "questions": [
            {
                "id": "q1",
                "type": "single_choice",
                "stem": "在顺序表中，访问第 i 个元素的时间复杂度是？",
                "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                "answer": 0,
                "analysis": "顺序表支持按下标随机访问，因此是 O(1)。",
            },
            {
                "id": "q2",
                "type": "single_choice",
                "stem": "以下哪种结构更适合实现队列？",
                "options": ["顺序表", "链表", "栈", "树"],
                "answer": 1,
                "analysis": "链表可以方便地在队头/队尾进行插入删除，适合队列实现。",
            },
        ],
    }


# === 前端静态文件路由（必须在 API 路由之后，通配路由之前） ===
@app.get("/")
async def serve_index():
    """
    返回打包后的前端 index.html
    """
    index_path = index_html_path()
    if not os.path.isfile(index_path):
        # 前端还没打包好的情况，用一个简单文本提示
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(
            "React 前端尚未构建，请先在 frontend/ 目录运行 `npm run build` 再重试。",
            status_code=500,
        )
    return FileResponse(index_path)


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    将所有非 /api、/assets、/questions 开头的路径都指向前端的 index.html（支持 React Router 等）
    注意：这个通配路由必须在所有具体路由之后注册
    """
    # 排除已经被 mount 的路径和 API 路径
    if full_path.startswith("api/") or full_path.startswith("assets/") or full_path.startswith("questions/"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    index_path = index_html_path()
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        "React 前端尚未构建，请先在 frontend/ 目录运行 `npm run build` 再重试。",
        status_code=500,
    )


