from pydantic import BaseModel
from typing import Optional
from ..models.student import Gender


class StudentBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    gender: Gender
    group_id: int


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int

    class Config:
        from_attributes = True
