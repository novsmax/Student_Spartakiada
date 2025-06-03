# backend/app/schemas/results.py - ОБНОВЛЕННАЯ ВЕРСИЯ с поддержкой original_result
from pydantic import BaseModel
from typing import Optional, List


class StudentPerformanceBase(BaseModel):
    student_id: int
    sport_type_id: int
    competition_id: int
    judge_id: int
    points: float  # Баллы за место (будут пересчитываться автоматически)
    time_result: Optional[str] = None  # Время в формате "0:01:23.45"
    original_result: Optional[float] = None  # Исходный результат (время в секундах, очки за игру)


class StudentPerformanceCreate(BaseModel):
    student_id: int
    sport_type_id: int
    competition_id: int
    judge_id: int
    time_result: Optional[str] = None  # Для временных видов спорта
    original_result: Optional[float] = None  # Для очковых видов спорта


class StudentPerformanceUpdate(BaseModel):
    time_result: Optional[str] = None
    original_result: Optional[float] = None


class StudentPerformanceRead(StudentPerformanceBase):
    id: int

    class Config:
        from_attributes = True


class StudentPerformanceDetail(BaseModel):
    id: int
    student_name: str
    time_result: Optional[str]
    original_result: Optional[float]
    points: float

    class Config:
        from_attributes = True


class FacultyCompetitionResultRead(BaseModel):
    id: int
    faculty_id: int
    faculty_name: str
    faculty_abbreviation: str
    sport_type_id: int
    sport_type_name: str
    total_points: float
    place: int
    performances: List[StudentPerformanceDetail]

    class Config:
        from_attributes = True


class FacultyTotalPointsRead(BaseModel):
    id: int
    faculty_id: int
    faculty_name: str
    faculty_abbreviation: str
    total_points: float
    overall_place: int

    class Config:
        from_attributes = True


class CompetitionResultsFilter(BaseModel):
    sport_type_id: Optional[int] = None
    gender: Optional[str] = None