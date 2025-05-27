from pydantic import BaseModel
from typing import Optional, List


class StudentPerformanceBase(BaseModel):
    student_id: int
    sport_type_id: int
    competition_id: int
    judge_id: int
    points: float
    time_result: Optional[str] = None


class StudentPerformanceCreate(StudentPerformanceBase):
    pass


class StudentPerformanceUpdate(BaseModel):
    points: Optional[float] = None
    time_result: Optional[str] = None


class StudentPerformanceRead(StudentPerformanceBase):
    id: int

    class Config:
        from_attributes = True


class StudentPerformanceDetail(BaseModel):
    id: int
    student_name: str
    time_result: Optional[str]
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