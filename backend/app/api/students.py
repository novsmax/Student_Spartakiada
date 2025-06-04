# backend/app/api/students.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List, Optional

from ..database import get_db
from ..models import Student, Faculty, Group, Competition, Judge, User, Team, team_students
from ..schemas.student import StudentCreate, StudentRead, StudentFindOrCreateRequest, StudentFindOrCreateResponse

router = APIRouter()


@router.get("/", response_model=List[StudentRead])
def get_students(
        faculty_abbreviation: Optional[str] = Query(None),
        first_name: Optional[str] = Query(None),
        last_name: Optional[str] = Query(None),
        gender: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    """Поиск студентов по различным критериям"""
    query = db.query(Student).join(Group).join(Faculty)

    if faculty_abbreviation:
        query = query.filter(Faculty.abbreviation == faculty_abbreviation)

    if first_name:
        query = query.filter(Student.first_name.ilike(f"%{first_name}%"))

    if last_name:
        query = query.filter(Student.last_name.ilike(f"%{last_name}%"))

    if gender:
        query = query.filter(Student.gender == gender)

    students = query.all()
    return students

@router.get("/student_by_faculty", response_model=List[Dict])
def get_students_by_faculty_id(
        faculty_id: Optional[int] = Query(None),
        gender: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(Student).join(Group).join(Faculty)

    if faculty_id:
        query = query.filter(Faculty.id == faculty_id)

    if gender:
        query = query.filter(Student.gender == gender)

    students = query.all()

    result = []
    for student in students:
        query = db.query(Group).filter(Group.id == student.group_id)
        group = query.first()

        query = db.query(Faculty).filter(Faculty.id == faculty_id)
        faculty = query.first()

        result.append({
            'id': student.id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'middle_name': student.middle_name,
            'gender': student.gender,
            'group_id': student.group_id,
            'group_name': group.number,
            'faculty_name': faculty.abbreviation,
        })

    return result

@router.get("/team_by_sport_faculty", response_model=List[Dict])
def get_team_by_sport_faculty(
    db: Session = Depends(get_db), 
    faculty_id: Optional[int] = Query(None), 
    sport_type_id: Optional[int] = Query(None),
    gender: Optional[str] = Query(None),
):
    
    query = db.query(Student
        ).join(team_students, Student.id == team_students.c.student_id
        ).join(Team, team_students.c.team_id == Team.id
        ).options(
            joinedload(Student.group),
            joinedload(Student.teams).joinedload(Team.sport_type),
            joinedload(Student.teams).joinedload(Team.faculty)
        )

    if sport_type_id:
        query = query.filter(Team.sport_type_id == sport_type_id)
    
    if faculty_id:
        query = query.filter(Team.faculty_id == faculty_id)
    
    if gender:
        query = query.filter(Student.gender == gender)
    
    students = query.all()
    
    result = []
    for student in students:
        team = None
        for t in student.teams:
            if t.faculty_id == faculty_id and t.sport_type_id == sport_type_id:
                team = t
                break
        
        if team:
            result.append({
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'middle_name': student.middle_name,
                'gender': student.gender,
                'group_number': student.group.number if student.group else None,
                'sport_type_name': team.sport_type.name if team.sport_type else None,
                'faculty_name': team.faculty.name if team.faculty else None
            })
    
    return result

@router.post("/find-or-create/", response_model=StudentFindOrCreateResponse)
def find_or_create_student(
        request: StudentFindOrCreateRequest,
        db: Session = Depends(get_db)
):
    """Найти студента или создать нового если не существует"""

    # Парсим полное имя
    name_parts = request.full_name.strip().split()
    if len(name_parts) < 2:
        raise HTTPException(status_code=400, detail="Имя должно содержать минимум фамилию и имя")

    last_name = name_parts[0]
    first_name = name_parts[1]
    middle_name = name_parts[2] if len(name_parts) > 2 else None

    # Ищем факультет
    faculty = db.query(Faculty).filter(Faculty.abbreviation == request.faculty_abbreviation).first()
    if not faculty:
        raise HTTPException(status_code=404, detail=f"Факультет {request.faculty_abbreviation} не найден")

    # Ищем существующего студента
    student = db.query(Student).join(Group).join(Faculty).filter(
        Faculty.abbreviation == request.faculty_abbreviation,
        Student.first_name == first_name,
        Student.last_name == last_name,
        Student.gender == request.gender
    ).first()

    if student:
        return StudentFindOrCreateResponse(
            student_id=student.id,
            student_name=f"{student.last_name} {student.first_name}",
            faculty_id=faculty.id,
            faculty_name=faculty.name,
            created=False
        )

    # Создаем нового студента
    # Ищем первую доступную группу факультета
    group = db.query(Group).filter(Group.faculty_id == faculty.id).first()
    if not group:
        raise HTTPException(status_code=404, detail=f"Группы факультета {request.faculty_abbreviation} не найдены")

    new_student = Student(
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        gender=request.gender,
        group_id=group.id
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return StudentFindOrCreateResponse(
        student_id=new_student.id,
        student_name=f"{new_student.last_name} {new_student.first_name}",
        faculty_id=faculty.id,
        faculty_name=faculty.name,
        created=True
    )


@router.get("/judges/", response_model=List[dict])
def get_judges(sport_type_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Получить список судей"""
    query = db.query(Judge).join(User)

    if sport_type_id:
        query = query.filter(Judge.sport_type_id == sport_type_id)

    judges = query.all()

    result = []
    for judge in judges:
        result.append({
            "id": judge.id,
            "user_id": judge.user_id,
            "name": f"{judge.user.last_name} {judge.user.first_name}",
            "sport_type_id": judge.sport_type_id
        })

    return result


@router.post("/", response_model=StudentRead)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Создать нового студента"""
    db_student = Student(
        first_name=student.first_name,
        last_name=student.last_name,
        middle_name=student.middle_name,
        gender=student.gender,
        group_id=student.group_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Получить студента по ID"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student


@router.put("/{student_id}", response_model=StudentRead)
def update_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db)):
    """Обновить данные студента"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    db_student.first_name = student.first_name
    db_student.last_name = student.last_name
    db_student.middle_name = student.middle_name
    db_student.gender = student.gender
    db_student.group_id = student.group_id

    db.commit()
    db.refresh(db_student)
    return db_student


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Удалить студента"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    db.delete(db_student)
    db.commit()
    return {"message": "Студент успешно удален"}