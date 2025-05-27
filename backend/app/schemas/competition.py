from pydantic import BaseModel
from datetime import datetime
from typing import List


class CompetitionBase(BaseModel):
    name: str
    sport_type_id: int
    date: datetime
    location: str


class CompetitionCreate(CompetitionBase):
    team_ids: List[int]


class CompetitionRead(CompetitionBase):
    id: int

    class Config:
        from_attributes = True