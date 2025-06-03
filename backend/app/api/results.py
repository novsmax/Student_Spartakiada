# backend/app/api/results.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с правильным группированием команд по полу
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


def get_points_for_place(place):
    """Получить баллы за место согласно правилам спартакиады"""
    if place <= 10:
        return 11 - place  # 1 место = 10 баллов, 2 место = 9 баллов, ..., 10 место = 1 балл
    else:
        return 1  # 11+ места = 1 балл


def is_team_sport(sport_name):
    """Определить, является ли вид спорта командным"""
    team_sports = ['Баскетбол', 'Волейбол', 'Футбол']
    return any(sport in sport_name for sport in team_sports)


def recalculate_competition_points(db: Session, sport_type_id: int):
    """Пересчитать баллы для всех участников соревнования с раздельным подсчетом по полу"""

    # Получаем вид спорта
    sport_type = db.query(SportType).filter(SportType.id == sport_type_id).first()
    if not sport_type:
        return

    # Получаем все выступления по данному виду спорта
    performances = db.query(StudentPerformance).filter(
        StudentPerformance.sport_type_id == sport_type_id
    ).join(Student).join(Group).join(Faculty).all()

    if not performances:
        return

    is_team = is_team_sport(sport_type.name)
    is_time_based = any(word in sport_type.name.lower() for word in ['бег', 'плавание'])

    if is_team:
        # КОМАНДНЫЕ ВИДЫ СПОРТА - раздельно по полу
        # Разделяем команды по полу
        male_performances = [p for p in performances if p.student.gender.value == "М"]
        female_performances = [p for p in performances if p.student.gender.value == "Ж"]

        for gender_performances in [male_performances, female_performances]:
            if not gender_performances:
                continue

            # Группируем по факультетам внутри каждого пола
            faculty_performances = {}
            for perf in gender_performances:
                faculty_id = perf.student.group.faculty_id
                if faculty_id not in faculty_performances:
                    faculty_performances[faculty_id] = []
                faculty_performances[faculty_id].append(perf)

            # Сортируем команды по результатам
            faculty_results = []
            for faculty_id, perfs in faculty_performances.items():
                if is_time_based and perfs[0].time_result:
                    # Конвертируем время в секунды для сортировки
                    time_parts = perfs[0].time_result.split(':')
                    if len(time_parts) == 3:
                        total_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + float(time_parts[2])
                    else:
                        total_seconds = float(perfs[0].time_result)
                    sort_key = total_seconds
                else:
                    # Для очковых видов используем original_result
                    sort_key = -(perfs[0].original_result or 0)  # Отрицательное для сортировки по убыванию

                faculty_results.append((faculty_id, perfs, sort_key))

            # Сортируем команды одного пола
            faculty_results.sort(key=lambda x: x[2])

            # Присваиваем места и баллы внутри пола
            for place, (faculty_id, perfs, _) in enumerate(faculty_results, 1):
                points = get_points_for_place(place)
                # Всем членам команды одинаковые баллы
                for perf in perfs:
                    perf.points = points

    else:
        # ИНДИВИДУАЛЬНЫЕ ВИДЫ СПОРТА - раздельно по полу
        # Разделяем участников по полу
        male_performances = [p for p in performances if p.student.gender.value == "М"]
        female_performances = [p for p in performances if p.student.gender.value == "Ж"]

        for gender_performances in [male_performances, female_performances]:
            if not gender_performances:
                continue

            if is_time_based:
                # Сортируем по времени (меньше = лучше)
                def time_to_seconds(time_str):
                    if not time_str:
                        return float('inf')
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    return float(time_str)

                gender_performances.sort(key=lambda p: time_to_seconds(p.time_result))
            else:
                # Сортируем по исходному результату (больше = лучше)
                gender_performances.sort(key=lambda p: p.original_result or 0, reverse=True)

            # Присваиваем места и пересчитываем баллы внутри пола
            current_place = 1
            for i, performance in enumerate(gender_performances):
                if i > 0:
                    prev_perf = gender_performances[i - 1]
                    if is_time_based:
                        if performance.time_result != prev_perf.time_result:
                            current_place = i + 1
                    else:
                        # Сравниваем исходные результаты
                        if (performance.original_result or 0) != (prev_perf.original_result or 0):
                            current_place = i + 1

                # Присваиваем баллы согласно месту внутри пола
                performance.points = get_points_for_place(current_place)

    db.commit()


@router.get("/competition-results/", response_model=List[dict])
def get_competition_results(
        sport_type_id: Optional[int] = Query(None),
        gender: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Получить результаты соревнований
    При gender=None показывает общий протокол с абсолютными результатами И баллами
    При gender=М/Ж показывает раздельный подсчет с баллами за места
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
        # Пересчитываем баллы для этого вида спорта (нужно для раздельного подсчета)
        recalculate_competition_points(db, sport_type_id)

    if gender:
        query = query.filter(Student.gender == gender)

    performances = query.all()

    if not performances:
        return []

    # Определяем тип спорта
    sport_type = performances[0].sport_type if performances else None
    is_team = sport_type and is_team_sport(sport_type.name)
    is_time_based = sport_type and any(word in sport_type.name.lower() for word in ['бег', 'плавание'])

    results = []

    if gender:
        # РАЗДЕЛЬНЫЙ ПОДСЧЕТ ПО ПОЛУ - показываем баллы за места внутри пола
        if is_team and sport_type_id:
            # Командные виды спорта для одного пола - группируем по факультетам
            faculty_performances = {}
            for perf in performances:
                faculty_id = perf.student.group.faculty_id
                if faculty_id not in faculty_performances:
                    faculty_performances[faculty_id] = {
                        'faculty': perf.student.group.faculty,
                        'performances': [],
                        'points': perf.points
                    }
                faculty_performances[faculty_id]['performances'].append(perf)

            # Сортируем команды по баллам
            sorted_faculties = sorted(faculty_performances.items(),
                                      key=lambda x: x[1]['points'],
                                      reverse=True)

            # Определяем места
            current_place = 1
            for i, (faculty_id, data) in enumerate(sorted_faculties):
                if i > 0:
                    prev_points = sorted_faculties[i - 1][1]['points']
                    if data['points'] != prev_points:
                        current_place = i + 1

                # Добавляем результаты для каждого члена команды
                for perf in data['performances']:
                    student = perf.student
                    student_name = f"{student.last_name} {student.first_name[0]}."
                    if student.middle_name:
                        student_name += f"{student.middle_name[0]}."

                    results.append({
                        "place": current_place,
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
                        "is_team_sport": True,
                        "original_result": perf.original_result
                    })
        else:
            # Индивидуальные виды спорта для одного пола
            if is_time_based:
                def time_to_seconds(time_str):
                    if not time_str:
                        return float('inf')
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    return float(time_str)

                performances.sort(key=lambda p: time_to_seconds(p.time_result))
            else:
                performances.sort(key=lambda p: p.original_result or 0, reverse=True)

            # Определяем места
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
                        if (performance.original_result or 0) != (prev_perf.original_result or 0):
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
                    "is_team_sport": False,
                    "original_result": performance.original_result
                })
    else:
        # ОБЩИЙ ПРОТОКОЛ - показываем абсолютные результаты И баллы
        if is_team and sport_type_id:
            # Командные виды спорта - ИСПРАВЛЕНО: группируем по факультету И полу
            faculty_performances = {}
            for perf in performances:
                # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: группируем по факультету И полу
                faculty_gender_key = f"{perf.student.group.faculty_id}_{perf.student.gender.value}"
                if faculty_gender_key not in faculty_performances:
                    faculty_performances[faculty_gender_key] = {
                        'faculty': perf.student.group.faculty,
                        'gender': perf.student.gender.value,
                        'performances': [],
                        'original_result': perf.original_result,
                        'time_result': perf.time_result,
                        'points': perf.points
                    }
                faculty_performances[faculty_gender_key]['performances'].append(perf)

            # Сортируем команды по абсолютным результатам
            faculty_list = list(faculty_performances.items())
            if is_time_based:
                def time_to_seconds(time_str):
                    if not time_str:
                        return float('inf')
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    return float(time_str)

                faculty_list.sort(key=lambda x: time_to_seconds(x[1]['time_result']))
            else:
                faculty_list.sort(key=lambda x: x[1]['original_result'] or 0, reverse=True)

            # Присваиваем места по абсолютным результатам
            current_place = 1
            for i, (key, data) in enumerate(faculty_list):
                if i > 0:
                    prev_data = faculty_list[i - 1][1]
                    if is_time_based:
                        if data['time_result'] != prev_data['time_result']:
                            current_place = i + 1
                    else:
                        if (data['original_result'] or 0) != (prev_data['original_result'] or 0):
                            current_place = i + 1

                # ИСПРАВЛЕНО: показываем команду с указанием пола
                team_name = f"{data['faculty'].abbreviation} ({data['gender']})"

                for perf in data['performances']:
                    student = perf.student
                    student_name = f"{student.last_name} {student.first_name[0]}."
                    if student.middle_name:
                        student_name += f"{student.middle_name[0]}."

                    results.append({
                        "place": current_place,
                        "faculty_id": data['faculty'].id,
                        "faculty_name": data['faculty'].name,
                        "faculty_abbreviation": team_name,  # Команда с указанием пола
                        "student_id": student.id,
                        "student_name": student_name,
                        "gender": student.gender.value,
                        "time_result": perf.time_result,
                        "points": perf.points,
                        "performance_id": perf.id,
                        "sport_type_id": perf.sport_type_id,
                        "sport_type_name": perf.sport_type.name,
                        "is_team_sport": True,
                        "original_result": perf.original_result
                    })
        else:
            # Индивидуальные виды спорта - общий протокол всех участников
            if is_time_based:
                def time_to_seconds(time_str):
                    if not time_str:
                        return float('inf')
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    return float(time_str)

                performances.sort(key=lambda p: time_to_seconds(p.time_result))
            else:
                performances.sort(key=lambda p: p.original_result or 0, reverse=True)

            # Присваиваем места по абсолютным результатам
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
                        if (performance.original_result or 0) != (prev_perf.original_result or 0):
                            current_place = i + 1

                student_name = f"{student.last_name} {student.first_name[0]}."
                if student.middle_name:
                    student_name += f"{student.middle_name[0]}."

                # Добавляем пол к имени
                student_name_with_gender = f"{student_name} ({student.gender.value})"

                results.append({
                    "place": current_place,
                    "faculty_id": faculty.id,
                    "faculty_name": faculty.name,
                    "faculty_abbreviation": faculty.abbreviation,
                    "student_id": student.id,
                    "student_name": student_name_with_gender,
                    "gender": student.gender.value,
                    "time_result": performance.time_result,
                    "points": performance.points,
                    "performance_id": performance.id,
                    "sport_type_id": performance.sport_type_id,
                    "sport_type_name": performance.sport_type.name,
                    "is_team_sport": False,
                    "original_result": performance.original_result
                })

    return results


@router.get("/faculty-sport-rating/", response_model=List[dict])
def get_faculty_sport_rating(
        sport_type_id: Optional[int] = Query(None),
        gender: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Получить рейтинг факультетов с учетом раздельного подсчета по полу
    """
    if sport_type_id:
        # Пересчитываем баллы перед формированием рейтинга
        recalculate_competition_points(db, sport_type_id)

        # Рейтинг по конкретному виду спорта с учетом пола
        query = db.query(
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
        )

        if gender:
            query = query.filter(Student.gender == gender)

        results = query.group_by(
            Faculty.id, Faculty.name, Faculty.abbreviation
        ).order_by(
            desc('total_points')
        ).all()

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
        missing_query = db.query(Faculty).filter(~Faculty.id.in_(faculty_ids))

        if gender:
            missing_query = missing_query.join(Group).join(Student).filter(
                Student.gender == gender
            ).distinct()

        missing_faculties = missing_query.all()

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
        # Общий рейтинг с учетом пола
        if gender:
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
                Student.gender == gender
            ).group_by(
                Faculty.id, Faculty.name, Faculty.abbreviation
            ).order_by(
                desc('total_points')
            ).all()

            rating = []
            for i, result in enumerate(results, 1):
                rating.append({
                    "place": i,
                    "faculty_id": result.id,
                    "faculty_name": result.name,
                    "faculty_abbreviation": result.abbreviation,
                    "total_points": float(result.total_points) if result.total_points else 0,
                    "sport_type_id": None
                })

            return rating
        else:
            # Пересчитываем общие результаты
            update_faculty_results_all(db)

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


@router.post("/recalculate-points/")
def recalculate_all_points(db: Session = Depends(get_db)):
    """Пересчитать баллы для всех соревнований с раздельным подсчетом по полу"""
    sport_types = db.query(SportType).all()

    for sport_type in sport_types:
        recalculate_competition_points(db, sport_type.id)

    # Обновляем общие результаты
    update_faculty_results_all(db)

    return {"message": "Points recalculated successfully with gender separation"}


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

    # Создаем выступление с временными баллами (будут пересчитаны)
    db_performance = StudentPerformance(
        student_id=performance.student_id,
        sport_type_id=performance.sport_type_id,
        competition_id=performance.competition_id,
        judge_id=performance.judge_id,
        points=0,  # Временное значение, будет пересчитано
        time_result=performance.time_result,
        original_result=performance.original_result
    )
    db.add(db_performance)
    db.commit()

    # Пересчитываем баллы для этого вида спорта
    recalculate_competition_points(db, performance.sport_type_id)

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

    # Пересчитываем баллы для оставшихся участников
    recalculate_competition_points(db, sport_type_id)

    # Обновляем результаты факультетов
    update_faculty_results(db, sport_type_id)

    return {"message": "Performance deleted successfully"}


def update_faculty_results(db: Session, sport_type_id: int):
    """Update faculty results for a specific sport type"""
    faculties = db.query(Faculty).all()

    for faculty in faculties:
        total_points = db.query(func.sum(StudentPerformance.points)).join(
            Student
        ).join(
            Group
        ).filter(
            Group.faculty_id == faculty.id,
            StudentPerformance.sport_type_id == sport_type_id
        ).scalar() or 0

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


def update_faculty_results_all(db: Session):
    """Update results for all sport types"""
    sport_types = db.query(SportType).all()

    for sport_type in sport_types:
        update_faculty_results(db, sport_type.id)

    update_total_points(db)


def update_total_points(db: Session):
    """Update total points for all faculties across all sports"""
    faculties = db.query(Faculty).all()

    for faculty in faculties:
        total_points = db.query(func.sum(FacultyCompetitionResult.total_points)).filter(
            FacultyCompetitionResult.faculty_id == faculty.id
        ).scalar() or 0

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

    faculty_totals = db.query(FacultyTotalPoints).order_by(
        FacultyTotalPoints.total_points.desc()
    ).all()

    for i, total in enumerate(faculty_totals, 1):
        total.overall_place = i

    db.commit()


@router.get("/spartakiada-rating/", response_model=List[FacultyTotalPointsRead])
def get_spartakiada_rating(db: Session = Depends(get_db)):
    """Получить общий рейтинг спартакиады"""
    # Пересчитываем все результаты
    update_faculty_results_all(db)

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