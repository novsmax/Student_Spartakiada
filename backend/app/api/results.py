from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from ..database import get_db
from ..models import (
    StudentPerformance, FacultyCompetitionResult, FacultyTotalPoints,
    Student, Faculty, SportType, Competition, Team
)
from ..schemas import (
    StudentPerformanceCreate, StudentPerformanceRead, StudentPerformanceUpdate,
    FacultyCompetitionResultRead, FacultyTotalPointsRead,
    CompetitionResultsFilter, StudentPerformanceDetail
)
from .auth import get_current_user

router = APIRouter()


@router.post("/performances/", response_model=StudentPerformanceRead)
def create_performance(
        performance: StudentPerformanceCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    # Check if performance already exists
    existing = db.query(StudentPerformance).filter(
        StudentPerformance.student_id == performance.student_id,
        StudentPerformance.competition_id == performance.competition_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Performance already exists for this student in this competition")

    db_performance = StudentPerformance(**performance.dict())
    db.add(db_performance)
    db.commit()

    # Update faculty results
    update_faculty_results(db, performance.sport_type_id)

    db.refresh(db_performance)
    return db_performance


@router.put("/performances/{performance_id}", response_model=StudentPerformanceRead)
def update_performance(
        performance_id: int,
        performance_update: StudentPerformanceUpdate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    db_performance = db.query(StudentPerformance).filter(StudentPerformance.id == performance_id).first()
    if not db_performance:
        raise HTTPException(status_code=404, detail="Performance not found")

    for key, value in performance_update.dict(exclude_unset=True).items():
        setattr(db_performance, key, value)

    db.commit()

    # Update faculty results
    update_faculty_results(db, db_performance.sport_type_id)

    db.refresh(db_performance)
    return db_performance


@router.delete("/performances/{performance_id}")
def delete_performance(
        performance_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    db_performance = db.query(StudentPerformance).filter(StudentPerformance.id == performance_id).first()
    if not db_performance:
        raise HTTPException(status_code=404, detail="Performance not found")

    sport_type_id = db_performance.sport_type_id
    db.delete(db_performance)
    db.commit()

    # Update faculty results
    update_faculty_results(db, sport_type_id)

    return {"message": "Performance deleted successfully"}


@router.get("/competition-results/", response_model=List[FacultyCompetitionResultRead])
def get_competition_results(
        sport_type_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(FacultyCompetitionResult).options(
        joinedload(FacultyCompetitionResult.faculty),
        joinedload(FacultyCompetitionResult.sport_type),
        joinedload(FacultyCompetitionResult.performances).joinedload(StudentPerformance.student)
    )

    if sport_type_id:
        query = query.filter(FacultyCompetitionResult.sport_type_id == sport_type_id)

    results = query.order_by(FacultyCompetitionResult.place).all()

    # Convert to response model with detailed performance info
    response = []
    for result in results:
        performances = []
        for perf in result.performances:
            performances.append(StudentPerformanceDetail(
                id=perf.id,
                student_name=f"{perf.student.last_name} {perf.student.first_name[0]}.{perf.student.middle_name[0] if perf.student.middle_name else ''}",
                time_result=perf.time_result,
                points=perf.points
            ))

        response.append(FacultyCompetitionResultRead(
            id=result.id,
            faculty_id=result.faculty_id,
            faculty_name=result.faculty.name,
            faculty_abbreviation=result.faculty.abbreviation,
            sport_type_id=result.sport_type_id,
            sport_type_name=result.sport_type.name,
            total_points=result.total_points,
            place=result.place,
            performances=performances
        ))

    return response


@router.get("/spartakiada-rating/", response_model=List[FacultyTotalPointsRead])
def get_spartakiada_rating(db: Session = Depends(get_db)):
    results = db.query(FacultyTotalPoints).options(
        joinedload(FacultyTotalPoints.faculty)
    ).order_by(FacultyTotalPoints.overall_place).all()

    response = []
    for result in results:
        response.append(FacultyTotalPointsRead(
            id=result.id,
            faculty_id=result.faculty_id,
            faculty_name=result.faculty.name,
            faculty_abbreviation=result.faculty.abbreviation,
            total_points=result.total_points,
            overall_place=result.overall_place
        ))

    return response


def update_faculty_results(db: Session, sport_type_id: int):
    """Update faculty results for a specific sport type"""
    # Get all faculties
    faculties = db.query(Faculty).all()

    for faculty in faculties:
        # Calculate total points for faculty in this sport
        total_points = db.query(func.sum(StudentPerformance.points)).join(
            Student
        ).join(
            Team, Student.teams
        ).filter(
            Team.faculty_id == faculty.id,
            StudentPerformance.sport_type_id == sport_type_id
        ).scalar() or 0

        # Update or create faculty competition result
        faculty_result = db.query(FacultyCompetitionResult).filter(
            FacultyCompetitionResult.faculty_id == faculty.id,
            FacultyCompetitionResult.sport_type_id == sport_type_id
        ).first()

        if not faculty_result:
            faculty_result = FacultyCompetitionResult(
                faculty_id=faculty.id,
                sport_type_id=sport_type_id,
                total_points=total_points
            )
            db.add(faculty_result)
        else:
            faculty_result.total_points = total_points

    db.commit()

    # Update places
    faculty_results = db.query(FacultyCompetitionResult).filter(
        FacultyCompetitionResult.sport_type_id == sport_type_id
    ).order_by(FacultyCompetitionResult.total_points.desc()).all()

    for i, result in enumerate(faculty_results, 1):
        result.place = i

    db.commit()

    # Update total points for all faculties
    update_total_points(db)


def update_total_points(db: Session):
    """Update total points for all faculties across all sports"""
    faculties = db.query(Faculty).all()

    for faculty in faculties:
        # Calculate total points across all sports
        total_points = db.query(func.sum(FacultyCompetitionResult.total_points)).filter(
            FacultyCompetitionResult.faculty_id == faculty.id
        ).scalar() or 0

        # Update or create total points
        faculty_total = db.query(FacultyTotalPoints).filter(
            FacultyTotalPoints.faculty_id == faculty.id
        ).first()

        if not faculty_total:
            faculty_total = FacultyTotalPoints(
                faculty_id=faculty.id,
                total_points=total_points
            )
            db.add(faculty_total)
        else:
            faculty_total.total_points = total_points

    db.commit()

    # Update overall places
    faculty_totals = db.query(FacultyTotalPoints).order_by(
        FacultyTotalPoints.total_points.desc()
    ).all()

    for i, total in enumerate(faculty_totals, 1):
        total.overall_place = i

    db.commit()