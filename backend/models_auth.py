from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    email: Optional[str] = None
    disabled: bool = Field(default=False)
    is_guest: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
