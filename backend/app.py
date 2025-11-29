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
from .models import Course, Chapter, Quiz, Question, QuizReadWithQuestions
from .services import parse_chapters_from_pdf, generate_quiz_for_chapter, save_quiz_to_db
import shutil
from pathlib import Path

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
async def upload_file(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    上传 PDF 文件，创建 Course 记录
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # 保存文件到 data 目录
    upload_dir = Path("data")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 创建数据库记录
    # 简单起见，用文件名作为课程标题
    course_title = file.filename.replace(".pdf", "")
    course = Course(title=course_title, description="Uploaded via Web")
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return {"status": "success", "course_id": course.id, "filename": file.filename}

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
        chapters_data = parse_chapters_from_pdf(str(pdf_path))
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
            
            # 3. 保存题目
            save_quiz_to_db(session, chapter.id, quiz_data)
            print(f"[Task] Saved quiz for chapter: {chapter.title}")
            
        # Update course status
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
        chapters_data = parse_chapters_from_pdf(str(pdf_path))
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
        
        # Update course status
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
        
        # Get chapters
        statement = select(Chapter).where(Chapter.course_id == course_id)
        if config.get("chapter_ids"):
             statement = statement.where(Chapter.id.in_(config["chapter_ids"]))
        
        chapters = session.exec(statement).all()
        print(f"[Task] Generating for {len(chapters)} chapters")

        for chapter in chapters:
             # 2. 生成题目
            print(f"[Task] Generating quiz for chapter: {chapter.title}")
            # Pass custom counts if supported by service (need to update service)
            # For now, we use default or update service.
            # Let's assume we update service to accept counts.
            quiz_data = generate_quiz_for_chapter(
                chapter.content_text, 
                chapter.title,
                num_mc=config.get("num_mc", 5),
                num_fb=config.get("num_fb", 5)
            )
            
            # 3. 保存题目
            save_quiz_to_db(session, chapter.id, quiz_data)
            print(f"[Task] Saved quiz for chapter: {chapter.title}")

        # Update course status
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


@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Delete associated files (optional, but good practice)
    # Assuming we stored filename or can derive it. 
    # Current model doesn't store filename explicitly other than title maybe.
    # Let's skip file deletion for now to avoid deleting wrong files, 
    # or we can add filename to Course model later.
    return {"status": "accepted", "message": "Generation task started"}

def run_generation_task(course_id: int, filename: str):
    """
    Wrapper to create a new session for the background task
    """
    from .database import engine
    with Session(engine) as session:
        process_course_generation(course_id, filename, session)

@app.get("/api/courses/{course_id}/chapters", response_model=list[Chapter])
async def get_course_chapters(course_id: int, session: Session = Depends(get_session)):
    chapters = session.exec(select(Chapter).where(Chapter.course_id == course_id)).all()
    return chapters

@app.get("/api/chapters/{chapter_id}/quiz", response_model=list[QuizReadWithQuestions])
async def get_chapter_quiz(chapter_id: int, session: Session = Depends(get_session)):
    quizzes = session.exec(select(Quiz).where(Quiz.chapter_id == chapter_id)).all()
    return quizzes

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


