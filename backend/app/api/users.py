# backend/app/api/users.py - ПОЛНАЯ ВЕРСИЯ
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, Judge, Teacher, Faculty, Group, SportType
from ..schemas import UserCreate, UserRead
from ..api.auth import get_current_user, get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UserRead])
def get_users(
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список пользователей (только для админов)"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user


@router.get("/{user_id}", response_model=UserRead)
def get_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить пользователя по ID"""
    # Пользователи могут видеть только свою информацию, админы - всех
    if current_user.role.value != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/", response_model=UserRead)
def create_user(
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создать нового пользователя (только для админов)"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    # Проверяем, что пользователь с таким username не существует
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    # Создаем пользователя
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
        user_id: int,
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить пользователя"""
    # Пользователи могут обновлять только свою информацию, админы - всех
    if current_user.role.value != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Обновляем поля
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db_user.middle_name = user.middle_name
    db_user.username = user.username

    # Обновляем пароль только если он предоставлен
    if user.password:
        db_user.hashed_password = get_password_hash(user.password)

    # Только админы могут менять роли
    if current_user.role.value == "admin":
        db_user.role = user.role

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Удалить пользователя (только для админов)"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Нельзя удалить самого себя
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")

    db.delete(db_user)
    db.commit()
    return {"message": "Пользователь успешно удален"}


@router.post("/{user_id}/assign-judge")
def assign_user_as_judge(
        user_id: int,
        sport_type_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Назначить пользователя судьей по виду спорта"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем существование вида спорта
    sport_type = db.query(SportType).filter(SportType.id == sport_type_id).first()
    if not sport_type:
        raise HTTPException(status_code=404, detail="Вид спорта не найден")

    # Проверяем, что пользователь еще не является судьей
    existing_judge = db.query(Judge).filter(Judge.user_id == user_id).first()
    if existing_judge:
        # Обновляем вид спорта
        existing_judge.sport_type_id = sport_type_id
    else:
        # Создаем нового судью
        judge = Judge(user_id=user_id, sport_type_id=sport_type_id)
        db.add(judge)

    # Обновляем роль пользователя
    user.role = "judge"

    db.commit()
    return {"message": f"Пользователь {user.username} назначен судьей по {sport_type.name}"}


@router.post("/{user_id}/assign-teacher")
def assign_user_as_teacher(
        user_id: int,
        faculty_id: int,
        group_id: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Назначить пользователя преподавателем"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем существование факультета
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Факультет не найден")

    # Проверяем группу если указана
    if group_id:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Группа не найдена")
        if group.faculty_id != faculty_id:
            raise HTTPException(status_code=400, detail="Группа не принадлежит указанному факультету")

    # Проверяем, что пользователь еще не является преподавателем
    existing_teacher = db.query(Teacher).filter(Teacher.user_id == user_id).first()
    if existing_teacher:
        # Обновляем информацию
        existing_teacher.faculty_id = faculty_id
        existing_teacher.group_id = group_id
    else:
        # Создаем нового преподавателя
        teacher = Teacher(user_id=user_id, faculty_id=faculty_id, group_id=group_id)
        db.add(teacher)

    # Обновляем роль пользователя
    user.role = "teacher"

    db.commit()
    return {"message": f"Пользователь {user.username} назначен преподавателем {faculty.name}"}


@router.get("/judges/", response_model=List[dict])
def get_judges(db: Session = Depends(get_db)):
    """Получить список всех судей"""
    judges = db.query(Judge).join(User).join(SportType).all()

    result = []
    for judge in judges:
        result.append({
            "id": judge.id,
            "user_id": judge.user_id,
            "username": judge.user.username,
            "name": f"{judge.user.last_name} {judge.user.first_name}",
            "sport_type_id": judge.sport_type_id,
            "sport_type_name": judge.sport_type.name
        })

    return result


@router.get("/teachers/", response_model=List[dict])
def get_teachers(db: Session = Depends(get_db)):
    """Получить список всех преподавателей"""
    teachers = db.query(Teacher).join(User).join(Faculty).all()

    result = []
    for teacher in teachers:
        result.append({
            "id": teacher.id,
            "user_id": teacher.user_id,
            "username": teacher.user.username,
            "name": f"{teacher.user.last_name} {teacher.user.first_name}",
            "faculty_id": teacher.faculty_id,
            "faculty_name": teacher.faculty.name,
            "group_id": teacher.group_id
        })

    return result