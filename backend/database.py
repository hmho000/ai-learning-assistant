import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, text
from .models import *       # 业务模型 (Course, Chapter, etc.)
from .models_auth import *  # 认证模型 (User)

# 基础目录
BASE_DIR = Path("data")
BASE_DIR.mkdir(parents=True, exist_ok=True)

from sqlalchemy.pool import NullPool

# === 全局认证库 ===
AUTH_DB_FILE = BASE_DIR / "auth_main.db"
AUTH_DB_URL = f"sqlite:///{AUTH_DB_FILE}"
auth_engine = create_engine(AUTH_DB_URL, connect_args={"check_same_thread": False}, poolclass=NullPool)
with auth_engine.connect() as connection:
    connection.execute(text("PRAGMA journal_mode=WAL;"))

# 缓存用户引擎，避免重复创建导致连接池无法释放
_user_engines = {}

def init_auth_db():
    """初始化认证数据库 (User表)"""
    # 仅创建 User 表相关的部分
    # 注意：SQLModel.metadata.create_all 会创建所有导入的模型表
    # 为了避免混淆，最好区分 metadata，但简单起见，我们可以在这里通过 import 范围控制
    # 或者接受 auth_db里也有空业务表的冗余（SQLite很轻量，问题不大）
    # 但为了严谨，我们应该确保 models_auth 中的模型被注册，而 models 中的也许不需要在这里
    SQLModel.metadata.create_all(auth_engine)

def get_auth_session():
    """获取全局认证库的 Session"""
    with Session(auth_engine) as session:
        yield session

# === 用户个人库 ===
def get_user_db_path(user_id: int) -> Path:
    user_dir = BASE_DIR / "users" / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "learning.db"

def get_user_engine(user_id: int):
    """获取指定用户的数据库引擎 (带缓存)"""
    if user_id in _user_engines:
        return _user_engines[user_id]
        
    db_path = get_user_db_path(user_id)
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    # 核心修复：即使手动删除了 users 目录下的文件，再次获取引擎时也会自动重建表结构
    # create_all 是幂等的，表存在则跳过，不存在则补齐
    SQLModel.metadata.create_all(engine)
    
    _user_engines[user_id] = engine
    return engine


def remove_user_engine(user_id: int):
    """清理用户引擎 (关闭连接池)，用于删除数据库文件前"""
    if user_id in _user_engines:
        engine = _user_engines.pop(user_id)
        engine.dispose()

def init_user_db(user_id: int):
    """初始化用户的个人数据库"""
    engine = get_user_engine(user_id)
    SQLModel.metadata.create_all(engine)

# === 兼容旧代码 (暂时保留，后续删除) ===
# 为了防止直接报错，我们可以保留一个假的 get_session，但它应该抛出错误提醒开发者
def get_session():
    raise NotImplementedError("Global get_session is deprecated. Use get_current_user_session or get_auth_session.")

def create_db_and_tables():
    """默认初始化入口，现在只初始化 Global Auth DB"""
    init_auth_db()
