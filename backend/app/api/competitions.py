from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Competition, SportType, Team, Faculty, Group
from ..schemas import CompetitionCreate, CompetitionRead, SportTypeRead, FacultyRead, GroupRead

router = APIRouter()


@router.get("/sport-types/", response_model=List[SportTypeRead])
def get_sport_types(db: Session = Depends(get_db)):
    sport_types = db.query(SportType).all()
    return sport_types


@router.get("/", response_model=List[CompetitionRead])
def get_competitions(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    competitions = db.query(Competition).offset(skip).limit(limit).all()
    return competitions


@router.post("/", response_model=CompetitionRead)
def create_competition(
        competition: CompetitionCreate,
        db: Session = Depends(get_db)
):
    db_competition = Competition(
        name=competition.name,
        sport_type_id=competition.sport_type_id,
        date=competition.date,
        location=competition.location
    )
    db.add(db_competition)
    db.commit()

    # Add teams
    for team_id in competition.team_ids:
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            db_competition.teams.append(team)

    db.commit()
    db.refresh(db_competition)
    return db_competition


@router.get("/faculties/", response_model=List[FacultyRead])
def get_faculties(db: Session = Depends(get_db)):
    faculties = db.query(Faculty).all()
    return faculties


@router.get("/groups/", response_model=List[GroupRead])
def get_groups(
        faculty_id: int = None,
        db: Session = Depends(get_db)
):
    query = db.query(Group)
    if faculty_id:
        query = query.filter(Group.faculty_id == faculty_id)
    groups = query.all()
    return groups