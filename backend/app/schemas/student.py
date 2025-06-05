# backend/app/schemas/student.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
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


# НОВАЯ СХЕМА для поиска/создания студента
class StudentFindOrCreateRequest(BaseModel):
    faculty_abbreviation: str
    full_name: str
    gender: str


class StudentFindOrCreateResponse(BaseModel):
    student_id: int
    student_name: str
    faculty_id: int
    faculty_name: str
    created: bool

class StudentTeamCreate(BaseModel):
    student_id: int
    team_id: int