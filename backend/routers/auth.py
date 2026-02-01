from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta, datetime
from typing import Annotated, Optional, Union
import uuid
import shutil
from pathlib import Path

from ..database import get_auth_session, init_user_db, get_user_db_path
from ..models_auth import User
from ..security import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Token 接口定义
from pydantic import BaseModel
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None

# OAuth2 Scheme (用于Swagger UI鉴权)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, session: Session = Depends(get_auth_session)):
    # 1. 检查是否存在
    existing_user = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 2. 创建用户
    user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        email=user_in.email
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # 3. 初始化用户个人数据库
    try:
        init_user_db(user.id)
        # 同时创建文件目录
        files_dir = get_user_db_path(user.id).parent / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # 如果初始化失败，回滚用户创建（删除）
        session.delete(user)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize user database: {str(e)}"
        )

    # 4. 自动登录（返回Token）
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_auth_session)
):
    # form_data.username 和 form_data.password
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


# === 访客模式 & 清理逻辑 ===

def cleanup_expired_guests(session: Session):
    """清理过期访客 (2小时前创建的)"""
    cutoff_time = datetime.utcnow() - timedelta(hours=2)
    expired_guests = session.exec(
        select(User).where(User.is_guest == True, User.created_at < cutoff_time)
    ).all()
    
    deleted_count = 0
    for guest in expired_guests:
        print(f"[Cleanup] Removing expired guest: {guest.username} (ID: {guest.id}), Created: {guest.created_at}")
        # 1. 删除文件目录
        try:
            from ..database import remove_user_engine
            # 先关闭数据库连接
            try:
                remove_user_engine(guest.id)
            except Exception as e:
                print(f"[Cleanup] Error removing engine for {guest.id}: {e}")
            
            user_db_path = get_user_db_path(guest.id)
            user_dir = user_db_path.parent
            if user_dir.exists():
                shutil.rmtree(user_dir)
        except Exception as e:
            print(f"[Cleanup] Error removing files for {guest.id}: {e}")
        
        # 2. 删除 User 记录
        session.delete(guest)
        deleted_count += 1
    
    if deleted_count > 0:
        session.commit()
        print(f"[Cleanup] Removed {deleted_count} expired guests.")

class GuestLoginRequest(BaseModel):
    old_token: Optional[str] = None

@router.post("/guest-login", response_model=Token)
def guest_login(req: Optional[GuestLoginRequest] = Body(None), session: Session = Depends(get_auth_session)):
    print(f"[GuestLogin] Starting... (req: {req})")
    
    # 1. 触发一次清理
    try:
        cleanup_expired_guests(session)
    except Exception as e:
        print(f"[Warning] Cleanup failed: {e}")

    # 2. 尝试重用旧访客 Token
    if req and req.old_token:
        print(f"[GuestLogin] Attempting to reuse token: {req.old_token[:15]}...")
        user_id = decode_access_token(req.old_token)
        if user_id:
            try:
                user = session.get(User, int(user_id))
                if user and user.is_guest:
                    print(f"[GuestLogin] Reusing existing guest: {user.username} (ID: {user.id})")
                    # 更新创建时间，延长访客生命周期
                    user.created_at = datetime.utcnow()
                    session.add(user)
                    session.commit()
                    return {"access_token": req.old_token, "token_type": "bearer"}
                else:
                    print(f"[GuestLogin] Guest user {user_id} not found or not a guest.")
            except Exception as e:
                print(f"[GuestLogin] Error fetching user {user_id}: {e}")
        else:
            print(f"[GuestLogin] Invalid or expired token provided.")
    else:
        print("[GuestLogin] No old_token provided in request.")

    # 3. 创建新访客用户

    guest_username = f"guest_{uuid.uuid4().hex[:8]}"
    guest = User(
        username=guest_username,
        hashed_password="N/A", 
        is_guest=True
    )
    session.add(guest)
    session.commit()
    session.refresh(guest)
    print(f"[GuestLogin] Created new guest: {guest.username} (ID: {guest.id})")
    
    # 4. 初始化数据库
    try:
        init_user_db(guest.id)
        user_db_path = get_user_db_path(guest.id)
        files_dir = user_db_path.parent / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        session.delete(guest)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to init guest workspace"
        )

    # 5. 签发 Token
    access_token = create_access_token(subject=guest.id)
    return {"access_token": access_token, "token_type": "bearer"}


# 依赖项：获取当前用户
def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]) -> int:
    user_id_str = decode_access_token(token)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return int(user_id_str)

@router.get("/me")
def get_me(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_auth_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "is_guest": user.is_guest}

