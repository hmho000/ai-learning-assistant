from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# === 模型 ===

class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="processing")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 生成进度追踪
    generation_total_chapters: int = Field(default=0)
    generation_current_chapter: int = Field(default=0)
    generation_status_message: Optional[str] = Field(default=None)
    
    chapters: List["Chapter"] = Relationship(back_populates="course", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    title: str
    index: int  # 章节序号
    content_text: Optional[str] = Field(default=None) # 解析后的纯文本
    
    course: Course = Relationship(back_populates="chapters")
    quizzes: List["Quiz"] = Relationship(back_populates="chapter", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Quiz(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id")
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    chapter: Chapter = Relationship(back_populates="quizzes")
    questions: List["Question"] = Relationship(back_populates="quiz", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key="quiz.id")
    type: str  # "multiple_choice", "multi_select", "fill_in_blank", "true_false", "short_answer", "code"
    
    # 题目内容
    stem: str # 题干
    options_json: Optional[str] = None # JSON string for options ["A...", "B..."]（仅单选/多选题）
    answer: str
    explanation: Optional[str] = None
    
    quiz: Quiz = Relationship(back_populates="questions")

# === 读取模式 ===

class QuestionRead(SQLModel):
    id: int
    type: str
    stem: str
    options_json: Optional[str] = None
    answer: str
    explanation: Optional[str] = None

class QuizReadWithQuestions(SQLModel):
    id: int
    title: str
    description: Optional[str] = None
    questions: List[QuestionRead] = []

class ChapterRead(SQLModel):
    id: int
    title: str
    index: int
    has_quiz: bool = False


# 新增：错题记录表
class MistakeRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id") # 关联题目ID
    course_id: int = Field(foreign_key="course.id")     # 关联课程ID 
    created_at: datetime = Field(default_factory=datetime.utcnow) # 记录错题时间
    