from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from ..database import SessionLocal, engine, Base
from ..models import *
from ..api.auth import get_password_hash

# Таблица начисления баллов в зависимости от места
POINTS_BY_PLACE = {
    1: 10.0,  # 1 место
    2: 9.0,  # 2 место
    3: 8.0,  # 3 место
    4: 7.0,  # 4 место
    5: 6.0,  # 5 место
    6: 5.0,  # 6 место
    7: 4.0,  # 7 место
    8: 3.0,  # 8 место
    9: 2.0,  # 9 место
    10: 1.0,  # 10 место и далее
}


def get_points_for_place(place):
    """Получить баллы за место"""
    return POINTS_BY_PLACE.get(place, 1.0)


def is_team_sport(sport_name):
    """Определить, является ли вид спорта командным"""
    team_sports = ['Баскетбол', 'Волейбол', 'Футбол']
    return any(sport in sport_name for sport in team_sports)


def seed_database():
    db = SessionLocal()

    try:
        # Очистка существующих данных
        print("Очистка существующих данных...")
        db.query(StudentPerformance).delete()
        db.query(FacultyCompetitionResult).delete()
        db.query(FacultyTotalPoints).delete()
        db.query(Team).delete()
        db.query(Competition).delete()
        db.query(Student).delete()
        db.query(Teacher).delete()
        db.query(Judge).delete()
        db.query(Group).delete()
        db.query(SportType).delete()
        db.query(Faculty).delete()
        db.query(User).delete()
        db.commit()

        # Create faculties
        print("Создание факультетов...")
        faculties = [
            Faculty(name="Институт математики и информационных технологий", abbreviation="ИМИТ"),
            Faculty(name="Институт лингвистики и гуманитарных социальных наук", abbreviation="ИЛГИСН"),
            Faculty(name="Факультет технологий и инноваций", abbreviation="ФТИ"),
            Faculty(name="Медицинский институт", abbreviation="МедИН"),
            Faculty(name="Институт инженерных и инновационных технологий", abbreviation="ИИИТ"),
        ]
        for faculty in faculties:
            db.add(faculty)
        db.commit()

        # Create groups
        print("Создание групп...")
        groups = []
        for faculty in faculties:
            for i in range(1, 4):  # 3 groups per faculty
                group = Group(
                    number=f"{faculty.abbreviation}-{i}0{i}",
                    faculty_id=faculty.id
                )
                groups.append(group)
                db.add(group)
        db.commit()

        # Create sport types
        print("Создание видов спорта...")
        sport_types = [
            SportType(name="Бег 100м"),
            SportType(name="Бег 1000м"),
            SportType(name="Плавание"),
            SportType(name="Баскетбол"),
            SportType(name="Волейбол"),
            SportType(name="Футбол"),
            SportType(name="Шахматы"),
            SportType(name="Настольный теннис"),
        ]
        for sport_type in sport_types:
            db.add(sport_type)
        db.commit()

        # Create admin user (для совместимости, хотя авторизация отключена)
        print("Создание пользователей...")
        admin = User(
            first_name="Админ",
            last_name="Админов",
            middle_name="Админович",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin)

        # Create judges
        judges = []
        judge_names = [
            ("Иван", "Петров", "Сергеевич"),
            ("Мария", "Сидорова", "Александровна"),
            ("Алексей", "Кузнецов", "Владимирович"),
            ("Елена", "Новикова", "Андреевна"),
        ]
        for i, (first, last, middle) in enumerate(judge_names):
            user = User(
                first_name=first,
                last_name=last,
                middle_name=middle,
                username=f"judge{i + 1}",
                hashed_password=get_password_hash("password123"),
                role="judge"
            )
            db.add(user)
            db.commit()

            judge = Judge(
                user_id=user.id,
                sport_type_id=sport_types[i % len(sport_types)].id
            )
            judges.append(judge)
            db.add(judge)
        db.commit()

        # Create students
        print("Создание студентов...")
        students = []
        student_names = [
            ("Александр", "Новожилов", "Андреевич", "М"),
            ("Екатерина", "Белова", "Дмитриевна", "Ж"),
            ("Сергей", "Черных", "Иванович", "М"),
            ("Анастасия", "Золотова", "Павловна", "Ж"),
            ("Максим", "Серебряков", "Олегович", "М"),
            ("Дарья", "Красникова", "Алексеевна", "Ж"),
            ("Артем", "Зайцев", "Николаевич", "М"),
            ("Полина", "Волкова", "Сергеевна", "Ж"),
            ("Илья", "Медведев", "Константинович", "М"),
            ("София", "Лисицына", "Андреевна", "Ж"),
        ]

        for group in groups:
            for j in range(10):  # 10 students per group
                name_data = student_names[j % len(student_names)]
                student = Student(
                    first_name=name_data[0],
                    last_name=name_data[1],
                    middle_name=name_data[2],
                    gender=name_data[3],
                    group_id=group.id
                )
                students.append(student)
                db.add(student)
        db.commit()

        # Create teams
        print("Создание команд...")
        teams = []
        for faculty in faculties:
            faculty_students = [s for s in students if s.group.faculty_id == faculty.id]
            for sport_type in sport_types:
                if is_team_sport(sport_type.name):
                    # Для командных видов спорта создаем команды
                    team = Team(
                        sport_type_id=sport_type.id,
                        faculty_id=faculty.id
                    )
                    db.add(team)
                    db.commit()

                    # Добавляем 5-7 студентов в команду
                    team_size = random.randint(5, 7)
                    selected_students = random.sample(faculty_students, min(team_size, len(faculty_students)))
                    for student in selected_students:
                        team.students.append(student)
                    teams.append(team)
        db.commit()

        # Create competitions
        print("Создание соревнований...")
        competitions = []
        base_date = datetime.now() - timedelta(days=30)
        locations = ["Спортзал №1", "Стадион", "Бассейн", "Спортзал №2", "Актовый зал"]

        for i, sport_type in enumerate(sport_types):
            competition = Competition(
                name=f"Соревнования по {sport_type.name}",
                sport_type_id=sport_type.id,
                date=base_date + timedelta(days=i * 3),
                location=locations[i % len(locations)]
            )
            db.add(competition)
            db.commit()

            # Add teams to competition для командных видов
            if is_team_sport(sport_type.name):
                sport_teams = [t for t in teams if t.sport_type_id == sport_type.id]
                for team in sport_teams:
                    competition.teams.append(team)
            competitions.append(competition)
        db.commit()

        # Create student performances with proper point allocation
        print("Создание результатов выступлений с правильным начислением баллов...")

        for competition in competitions:
            sport_type = competition.sport_type

            if is_team_sport(sport_type.name):
                # КОМАНДНЫЕ ВИДЫ СПОРТА
                # Генерируем результаты для команд
                team_results = []
                for team in competition.teams:
                    # Генерируем случайный результат команды
                    team_score = random.uniform(50, 100)  # Примерный счет
                    team_results.append((team, team_score))

                # Сортируем команды по результатам
                team_results.sort(key=lambda x: x[1], reverse=True)

                # Присваиваем места и баллы командам
                for place, (team, score) in enumerate(team_results, 1):
                    points = get_points_for_place(place)

                    # Всем членам команды одинаковые баллы
                    for student in team.students:
                        performance = StudentPerformance(
                            student_id=student.id,
                            sport_type_id=competition.sport_type_id,
                            competition_id=competition.id,
                            judge_id=random.choice(judges).id,
                            points=points,  # Одинаковые баллы для всей команды
                            time_result=None
                        )
                        db.add(performance)

            else:
                # ИНДИВИДУАЛЬНЫЕ ВИДЫ СПОРТА
                # Собираем всех участников
                all_participants = []

                for faculty in faculties:
                    faculty_students = [s for s in students if s.group.faculty_id == faculty.id]
                    # Выбираем 3-5 участников от факультета
                    participants = random.sample(faculty_students, min(random.randint(3, 5), len(faculty_students)))

                    for student in participants:
                        # Генерируем результат
                        if "100м" in sport_type.name:
                            # Время от 10 до 15 секунд
                            seconds = random.uniform(10, 15)
                            time_result = f"0:00:{seconds:.2f}"
                            sort_key = seconds  # Меньше - лучше
                        elif "1000м" in sport_type.name:
                            # Время от 2:30 до 4:00
                            total_seconds = random.uniform(150, 240)
                            minutes = int(total_seconds // 60)
                            seconds = int(total_seconds % 60)
                            time_result = f"0:{minutes:02d}:{seconds:02d}"
                            sort_key = total_seconds  # Меньше - лучше
                        elif "Плавание" in sport_type.name:
                            # Время от 1:30 до 2:00
                            total_seconds = random.uniform(90, 120)
                            minutes = int(total_seconds // 60)
                            seconds = int(total_seconds % 60)
                            time_result = f"0:{minutes:02d}:{seconds:02d}"
                            sort_key = total_seconds  # Меньше - лучше
                        else:
                            # Для шахмат, тенниса - очки
                            time_result = None
                            sort_key = -random.uniform(70, 100)  # Больше - лучше (отрицательное для сортировки)

                        all_participants.append({
                            'student': student,
                            'time_result': time_result,
                            'sort_key': sort_key
                        })

                # Сортируем участников по результатам
                all_participants.sort(key=lambda x: x['sort_key'])

                # Присваиваем места и баллы
                for place, participant in enumerate(all_participants, 1):
                    points = get_points_for_place(place)

                    performance = StudentPerformance(
                        student_id=participant['student'].id,
                        sport_type_id=competition.sport_type_id,
                        competition_id=competition.id,
                        judge_id=random.choice(judges).id,
                        points=points,  # Баллы в зависимости от места
                        time_result=participant['time_result']
                    )
                    db.add(performance)

        db.commit()

        # Calculate faculty results
        print("Расчет результатов факультетов...")
        from ..api.results import update_faculty_results, update_total_points
        for sport_type in sport_types:
            update_faculty_results(db, sport_type.id)
        update_total_points(db)

        print("База данных успешно заполнена тестовыми данными!")
        print(f"Создано:")
        print(f"  - Факультетов: {len(faculties)}")
        print(f"  - Групп: {len(groups)}")
        print(f"  - Студентов: {len(students)}")
        print(f"  - Видов спорта: {len(sport_types)}")
        print(f"  - Команд: {len(teams)}")
        print(f"  - Соревнований: {len(competitions)}")
        print(f"  - Выступлений: {db.query(StudentPerformance).count()}")

    except Exception as e:
        print(f"Ошибка при заполнении базы данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(bind=engine)
    seed_database()