from pydantic import BaseModel
from typing import List, Optional


class FacultyBase(BaseModel):
    name: str
    abbreviation: str


class FacultyCreate(FacultyBase):
    pass


class FacultyRead(FacultyBase):
    id: int

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    number: str
    faculty_id: int


class GroupCreate(GroupBase):
    pass


class GroupRead(GroupBase):
    id: int

    class Config:
        from_attributes = True