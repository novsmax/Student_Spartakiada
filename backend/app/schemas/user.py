from pydantic import BaseModel
from typing import Optional
from ..models.user import UserRole


class UserBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    username: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: UserRole
    user_id: int