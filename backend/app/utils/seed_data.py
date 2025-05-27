from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from ..database import SessionLocal, engine, Base
from ..models import *
from ..api.auth import get_password_hash


def seed_database():
    db = SessionLocal()

    try:
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

        groups = []
        for faculty in faculties:
            for i in range(1, 4):
                group = Group(
                    number=f"{faculty.abbreviation}-{i}0{i}",
                    faculty_id=faculty.id
                )
                groups.append(group)
                db.add(group)
        db.commit()

        # Create sport types
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

        admin = User(
            first_name="Админ",
            last_name="Админов",
            middle_name="Админович",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin)

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

        teachers = []
        teacher_names = [
            ("Николай", "Васильев", "Петрович"),
            ("Ольга", "Морозова", "Викторовна"),
            ("Дмитрий", "Соколов", "Игоревич"),
            ("Анна", "Лебедева", "Сергеевна"),
            ("Михаил", "Козлов", "Александрович"),
        ]
        for i, (first, last, middle) in enumerate(teacher_names):
            user = User(
                first_name=first,
                last_name=last,
                middle_name=middle,
                username=f"teacher{i + 1}",
                hashed_password=get_password_hash("password123"),
                role="teacher"
            )
            db.add(user)
            db.commit()

            teacher = Teacher(
                user_id=user.id,
                faculty_id=faculties[i].id,
                group_id=groups[i * 3].id
            )
            teachers.append(teacher)
            db.add(teacher)
        db.commit()

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
            for j in range(10):
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

        teams = []
        for faculty in faculties:
            faculty_students = [s for s in students if s.group.faculty_id == faculty.id]
            for sport_type in sport_types[:6]:
                team = Team(
                    sport_type_id=sport_type.id,
                    faculty_id=faculty.id
                )
                db.add(team)
                db.commit()

                team_size = random.randint(5, 7)
                selected_students = random.sample(faculty_students, min(team_size, len(faculty_students)))
                for student in selected_students:
                    team.students.append(student)
                teams.append(team)
        db.commit()

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

            sport_teams = [t for t in teams if t.sport_type_id == sport_type.id]
            for team in sport_teams:
                competition.teams.append(team)
            competitions.append(competition)
        db.commit()

        for competition in competitions:
            for team in competition.teams:
                for student in team.students:
                    if "100м" in competition.sport_type.name:
                        time_result = f"0:00:{random.randint(10, 15)}.{random.randint(0, 99):02d}"
                        points = random.uniform(8, 10)
                    elif "1000м" in competition.sport_type.name:
                        minutes = random.randint(2, 4)
                        seconds = random.randint(0, 59)
                        time_result = f"0:{minutes:02d}:{seconds:02d}"
                        points = random.uniform(6, 10)
                    elif "Плавание" in competition.sport_type.name:
                        time_result = f"0:01:{random.randint(30, 50)}.{random.randint(0, 99):02d}"
                        points = random.uniform(7, 10)
                    else:
                        time_result = None
                        points = random.uniform(5, 10)

                    sport_judges = [j for j in judges if j.sport_type_id == competition.sport_type_id]
                    if not sport_judges:
                        sport_judges = judges

                    performance = StudentPerformance(
                        student_id=student.id,
                        sport_type_id=competition.sport_type_id,
                        competition_id=competition.id,
                        judge_id=random.choice(sport_judges).id,
                        points=round(points, 2),
                        time_result=time_result
                    )
                    db.add(performance)
        db.commit()

        from ..api.results import update_faculty_results, update_total_points
        for sport_type in sport_types:
            update_faculty_results(db, sport_type.id)
        update_total_points(db)

        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_database()