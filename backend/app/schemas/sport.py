from pydantic import BaseModel
from typing import List


class SportTypeBase(BaseModel):
    name: str


class SportTypeCreate(SportTypeBase):
    pass


class SportTypeRead(SportTypeBase):
    id: int

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    sport_type_id: int
    faculty_id: int
    student_ids: List[int]


class TeamCreate(TeamBase):
    pass


class TeamRead(BaseModel):
    id: int
    sport_type_id: int
    faculty_id: int

    class Config:
        from_attributes = True