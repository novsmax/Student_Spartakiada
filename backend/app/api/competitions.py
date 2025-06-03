# backend/app/api/competitions.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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
        sport_type_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(Competition)

    if sport_type_id:
        query = query.filter(Competition.sport_type_id == sport_type_id)

    competitions = query.offset(skip).limit(limit).all()
    return competitions


@router.get("/by-sport/{sport_type_id}")
def get_competition_by_sport(sport_type_id: int, db: Session = Depends(get_db)):
    """Получить активное соревнование по виду спорта"""
    competition = db.query(Competition).filter(
        Competition.sport_type_id == sport_type_id
    ).first()

    if not competition:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")

    return {
        "id": competition.id,
        "name": competition.name,
        "sport_type_id": competition.sport_type_id,
        "date": competition.date,
        "location": competition.location
    }


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