# backend/app/api/results.py - ОБНОВЛЕННАЯ ВЕРСИЯ с командными видами спорта
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, desc, asc
from typing import List, Optional

from ..database import get_db
from ..models import (
    StudentPerformance, FacultyCompetitionResult, FacultyTotalPoints,
    Student, Faculty, SportType, Competition, Team, Group
)
from ..schemas import (
    StudentPerformanceCreate, StudentPerformanceRead, StudentPerformanceUpdate,
    FacultyCompetitionResultRead, FacultyTotalPointsRead,
    CompetitionResultsFilter, StudentPerformanceDetail
)

router = APIRouter()


def is_team_sport(sport_name):
    """Определить, является ли вид спорта командным"""
    team_sports = ['Баскетбол', 'Волейбол', 'Футбол']
    return any(sport in sport_name for sport in team_sports)


@router.get("/competition-results/", response_model=List[dict])
def get_competition_results(
        sport_type_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Получить результаты соревнований с учетом командных и индивидуальных видов
    """
    # Базовый запрос
    query = db.query(StudentPerformance).join(
        Student
    ).join(
        Group
    ).join(
        Faculty
    ).options(
        joinedload(StudentPerformance.student),
        joinedload(StudentPerformance.sport_type)
    )

    if sport_type_id:
        query = query.filter(StudentPerformance.sport_type_id == sport_type_id)

    performances = query.all()

    if not performances:
        return []

    # Определяем тип спорта
    sport_type = performances[0].sport_type if performances else None
    is_team = sport_type and is_team_sport(sport_type.name)
    is_time_based = sport_type and any(word in sport_type.name.lower() for word in ['бег', 'плавание'])

    results = []

    if is_team and sport_type_id:
        # КОМАНДНЫЕ ВИДЫ СПОРТА
        # Группируем по факультетам и определяем места для команд
        faculty_performances = {}

        for perf in performances:
            faculty_id = perf.student.group.faculty_id
            if faculty_id not in faculty_performances:
                faculty_performances[faculty_id] = {
                    'faculty': perf.student.group.faculty,
                    'performances': [],
                    'total_points': 0
                }
            faculty_performances[faculty_id]['performances'].append(perf)
            faculty_performances[faculty_id]['total_points'] = perf.points  # Все в команде имеют одинаковые баллы

        # Сортируем команды по баллам
        sorted_faculties = sorted(faculty_performances.items(),
                                  key=lambda x: x[1]['total_points'],
                                  reverse=True)

        # Присваиваем места командам
        current_place = 1
        for i, (faculty_id, data) in enumerate(sorted_faculties):
            if i > 0:
                prev_points = sorted_faculties[i - 1][1]['total_points']
                if data['total_points'] != prev_points:
                    current_place = i + 1

            # Добавляем результаты для каждого члена команды
            for perf in data['performances']:
                student = perf.student
                student_name = f"{student.last_name} {student.first_name[0]}."
                if student.middle_name:
                    student_name += f"{student.middle_name[0]}."

                results.append({
                    "place": current_place,  # Одинаковое место для всей команды
                    "faculty_id": faculty_id,
                    "faculty_name": data['faculty'].name,
                    "faculty_abbreviation": data['faculty'].abbreviation,
                    "student_id": student.id,
                    "student_name": student_name,
                    "gender": student.gender.value,
                    "time_result": perf.time_result,
                    "points": perf.points,
                    "performance_id": perf.id,
                    "sport_type_id": perf.sport_type_id,
                    "sport_type_name": perf.sport_type.name,
                    "is_team_sport": True
                })

        # Сортируем результаты сначала по месту, затем по факультету
        results.sort(key=lambda x: (x['place'], x['faculty_abbreviation'], x['student_name']))

    else:
        # ИНДИВИДУАЛЬНЫЕ ВИДЫ СПОРТА
        # Сортируем выступления
        if is_time_based:
            performances.sort(key=lambda p: (
                p.time_result if p.time_result else '99:99:99',
                -p.points
            ))
        else:
            performances.sort(key=lambda p: p.points, reverse=True)

        # Присваиваем места индивидуально
        current_place = 1
        for i, performance in enumerate(performances):
            student = performance.student
            faculty = student.group.faculty

            if i > 0:
                prev_perf = performances[i - 1]
                if is_time_based:
                    if performance.time_result != prev_perf.time_result:
                        current_place = i + 1
                else:
                    if performance.points != prev_perf.points:
                        current_place = i + 1

            student_name = f"{student.last_name} {student.first_name[0]}."
            if student.middle_name:
                student_name += f"{student.middle_name[0]}."

            results.append({
                "place": current_place,
                "faculty_id": faculty.id,
                "faculty_name": faculty.name,
                "faculty_abbreviation": faculty.abbreviation,
                "student_id": student.id,
                "student_name": student_name,
                "gender": student.gender.value,
                "time_result": performance.time_result,
                "points": performance.points,
                "performance_id": performance.id,
                "sport_type_id": performance.sport_type_id,
                "sport_type_name": performance.sport_type.name,
                "is_team_sport": False
            })

    return results


@router.get("/faculty-sport-rating/", response_model=List[dict])
def get_faculty_sport_rating(
        sport_type_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Получить рейтинг факультетов по конкретному виду спорта или общий
    """
    if sport_type_id:
        # Рейтинг по конкретному виду спорта
        results = db.query(
            Faculty.id,
            Faculty.name,
            Faculty.abbreviation,
            func.sum(StudentPerformance.points).label('total_points')
        ).join(
            Group, Faculty.id == Group.faculty_id
        ).join(
            Student, Group.id == Student.group_id
        ).join(
            StudentPerformance, Student.id == StudentPerformance.student_id
        ).filter(
            StudentPerformance.sport_type_id == sport_type_id
        ).group_by(
            Faculty.id, Faculty.name, Faculty.abbreviation
        ).order_by(
            desc('total_points')
        ).all()

        # Формируем ответ с местами
        rating = []
        for i, result in enumerate(results, 1):
            rating.append({
                "place": i,
                "faculty_id": result.id,
                "faculty_name": result.name,
                "faculty_abbreviation": result.abbreviation,
                "total_points": float(result.total_points) if result.total_points else 0,
                "sport_type_id": sport_type_id
            })

        # Добавляем факультеты без результатов
        faculty_ids = [r.id for r in results]
        missing_faculties = db.query(Faculty).filter(~Faculty.id.in_(faculty_ids)).all()
        for faculty in missing_faculties:
            rating.append({
                "place": len(rating) + 1,
                "faculty_id": faculty.id,
                "faculty_name": faculty.name,
                "faculty_abbreviation": faculty.abbreviation,
                "total_points": 0,
                "sport_type_id": sport_type_id
            })

        return rating
    else:
        # Общий рейтинг
        results = db.query(FacultyTotalPoints).options(
            joinedload(FacultyTotalPoints.faculty)
        ).order_by(FacultyTotalPoints.overall_place).all()

        rating = []
        for result in results:
            rating.append({
                "place": result.overall_place,
                "faculty_id": result.faculty_id,
                "faculty_name": result.faculty.name,
                "faculty_abbreviation": result.faculty.abbreviation,
                "total_points": result.total_points,
                "sport_type_id": None
            })

        return rating


@router.post("/performances/", response_model=StudentPerformanceRead)
def create_performance(
        performance: StudentPerformanceCreate,
        db: Session = Depends(get_db)
):
    # Проверка существования
    existing = db.query(StudentPerformance).filter(
        StudentPerformance.student_id == performance.student_id,
        StudentPerformance.competition_id == performance.competition_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Performance already exists for this student in this competition")

    db_performance = StudentPerformance(**performance.dict())
    db.add(db_performance)
    db.commit()

    # Обновляем результаты факультетов
    update_faculty_results(db, performance.sport_type_id)

    db.refresh(db_performance)
    return db_performance


@router.delete("/performances/{performance_id}")
def delete_performance(
        performance_id: int,
        db: Session = Depends(get_db)
):
    db_performance = db.query(StudentPerformance).filter(StudentPerformance.id == performance_id).first()
    if not db_performance:
        raise HTTPException(status_code=404, detail="Performance not found")

    sport_type_id = db_performance.sport_type_id
    db.delete(db_performance)
    db.commit()

    # Обновляем результаты факультетов
    update_faculty_results(db, sport_type_id)

    return {"message": "Performance deleted successfully"}


def update_faculty_results(db: Session, sport_type_id: int):
    """Update faculty results for a specific sport type"""
    faculties = db.query(Faculty).all()

    for faculty in faculties:
        # Подсчет очков для факультета
        total_points = db.query(func.sum(StudentPerformance.points)).join(
            Student
        ).join(
            Group
        ).filter(
            Group.faculty_id == faculty.id,
            StudentPerformance.sport_type_id == sport_type_id
        ).scalar() or 0

        # Обновление или создание результата факультета
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

    # Обновление мест
    faculty_results = db.query(FacultyCompetitionResult).filter(
        FacultyCompetitionResult.sport_type_id == sport_type_id
    ).order_by(FacultyCompetitionResult.total_points.desc()).all()

    for i, result in enumerate(faculty_results, 1):
        result.place = i

    db.commit()

    # Обновление общих очков
    update_total_points(db)


def update_total_points(db: Session):
    """Update total points for all faculties across all sports"""
    faculties = db.query(Faculty).all()

    for faculty in faculties:
        # Общие очки по всем видам спорта
        total_points = db.query(func.sum(FacultyCompetitionResult.total_points)).filter(
            FacultyCompetitionResult.faculty_id == faculty.id
        ).scalar() or 0

        # Обновление или создание общих очков
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

    # Обновление общих мест
    faculty_totals = db.query(FacultyTotalPoints).order_by(
        FacultyTotalPoints.total_points.desc()
    ).all()

    for i, total in enumerate(faculty_totals, 1):
        total.overall_place = i

    db.commit()


@router.get("/spartakiada-rating/", response_model=List[FacultyTotalPointsRead])
def get_spartakiada_rating(db: Session = Depends(get_db)):
    """Получить общий рейтинг спартакиады"""
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