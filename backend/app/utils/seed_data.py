from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from sqlalchemy import text
from ..database import SessionLocal, engine, Base
from ..models import *
from ..api.auth import get_password_hash


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


def generate_realistic_result(sport_name, gender, is_good_athlete=False):
    """Генерировать реалистичные результаты для разных видов спорта с учетом пола"""

    if "100м" in sport_name:
        # Время от 11 до 16 секунд
        if gender == "М":
            base_time = random.uniform(11.0, 14.5) if is_good_athlete else random.uniform(13.0, 16.0)
        else:
            base_time = random.uniform(12.5, 16.0) if is_good_athlete else random.uniform(14.5, 18.0)
        return f"0:00:{base_time:.2f}", base_time

    elif "1000м" in sport_name:
        # Время от 2:30 до 5:00
        if gender == "М":
            total_seconds = random.uniform(150, 240) if is_good_athlete else random.uniform(200, 300)
        else:
            total_seconds = random.uniform(180, 280) if is_good_athlete else random.uniform(220, 350)
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"0:{minutes:02d}:{seconds:02d}", total_seconds

    elif "Плавание" in sport_name:
        # Время от 1:00 до 2:30
        if gender == "М":
            total_seconds = random.uniform(60, 120) if is_good_athlete else random.uniform(90, 150)
        else:
            total_seconds = random.uniform(70, 130) if is_good_athlete else random.uniform(100, 180)
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"0:{minutes:02d}:{seconds:02d}", total_seconds

    elif sport_name in ['Баскетбол', 'Волейбол', 'Футбол']:
        # Для командных видов - результат команды
        team_score = random.uniform(60, 95) if is_good_athlete else random.uniform(40, 80)
        return None, team_score

    else:
        # Для шахмат, тенниса - очки от 0 до 100
        score = random.uniform(70, 95) if is_good_athlete else random.uniform(40, 85)
        return None, score


def seed_database():
    db = SessionLocal()

    try:
        # Очистка существующих данных в правильном порядке
        print("Очистка существующих данных...")

        # Сначала удаляем данные из таблиц, которые ссылаются на другие таблицы
        db.query(StudentPerformance).delete()
        db.query(FacultyCompetitionResult).delete()
        db.query(FacultyTotalPoints).delete()

        # Очищаем связующие таблицы many-to-many напрямую
        print("Очистка связующих таблиц...")

        # Очистка team_students
        db.execute(text("DELETE FROM team_students"))

        # Очистка competition_teams
        db.execute(text("DELETE FROM competition_teams"))

        # Очистка faculty_result_performances
        db.execute(text("DELETE FROM faculty_result_performances"))

        # Очистка total_points_results
        db.execute(text("DELETE FROM total_points_results"))

        # Теперь можно безопасно удалить основные таблицы
        db.query(Competition).delete()
        db.query(Team).delete()
        db.query(Student).delete()
        db.query(Teacher).delete()
        db.query(Judge).delete()
        db.query(Group).delete()
        db.query(SportType).delete()
        db.query(Faculty).delete()
        db.query(User).delete()

        db.commit()
        print("Данные успешно очищены")

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

        # Create admin user
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

        # Create students with equal gender distribution
        print("Создание студентов с равным распределением по полу...")
        students = []

        # Мужские имена
        male_names = [
            ("Александр", "Новожилов", "Андреевич"),
            ("Сергей", "Черных", "Иванович"),
            ("Максим", "Серебряков", "Олегович"),
            ("Артем", "Зайцев", "Николаевич"),
            ("Илья", "Медведев", "Константинович"),
            ("Дмитрий", "Волков", "Петрович"),
            ("Андрей", "Соколов", "Алексеевич"),
            ("Михаил", "Козлов", "Викторович"),
            ("Николай", "Морозов", "Сергеевич"),
            ("Владимир", "Лебедев", "Олегович"),
        ]

        # Женские имена
        female_names = [
            ("Екатерина", "Белова", "Дмитриевна"),
            ("Анастасия", "Золотова", "Павловна"),
            ("Дарья", "Красникова", "Алексеевна"),
            ("Полина", "Волкова", "Сергеевна"),
            ("София", "Лисицына", "Андреевна"),
            ("Мария", "Орлова", "Ивановна"),
            ("Анна", "Петрова", "Николаевна"),
            ("Елена", "Смирнова", "Андреевна"),
            ("Ольга", "Кузнецова", "Михайловна"),
            ("Наталья", "Попова", "Владимировна"),
        ]

        for group in groups:
            # По 5 мужчин и 5 женщин в каждой группе
            for j in range(5):
                # Мужчина
                male_name_data = male_names[j % len(male_names)]
                male_student = Student(
                    first_name=male_name_data[0],
                    last_name=male_name_data[1],
                    middle_name=male_name_data[2],
                    gender="М",
                    group_id=group.id
                )
                students.append(male_student)
                db.add(male_student)

                # Женщина
                female_name_data = female_names[j % len(female_names)]
                female_student = Student(
                    first_name=female_name_data[0],
                    last_name=female_name_data[1],
                    middle_name=female_name_data[2],
                    gender="Ж",
                    group_id=group.id
                )
                students.append(female_student)
                db.add(female_student)
        db.commit()

        # Create teams for team sports
        print("Создание команд...")
        teams = []
        for faculty in faculties:
            faculty_students = [s for s in students if s.group.faculty_id == faculty.id]
            male_students = [s for s in faculty_students if s.gender.value == "М"]
            female_students = [s for s in faculty_students if s.gender.value == "Ж"]

            for sport_type in sport_types:
                if is_team_sport(sport_type.name):
                    # Создаем мужскую команду
                    male_team = Team(
                        sport_type_id=sport_type.id,
                        faculty_id=faculty.id
                    )
                    db.add(male_team)
                    db.commit()

                    # Добавляем мужчин в команду
                    team_size = min(5, len(male_students))
                    selected_male_students = random.sample(male_students, team_size)
                    for student in selected_male_students:
                        male_team.students.append(student)
                    teams.append(male_team)

                    # Создаем женскую команду
                    female_team = Team(
                        sport_type_id=sport_type.id,
                        faculty_id=faculty.id
                    )
                    db.add(female_team)
                    db.commit()

                    # Добавляем женщин в команду
                    team_size = min(5, len(female_students))
                    selected_female_students = random.sample(female_students, team_size)
                    for student in selected_female_students:
                        female_team.students.append(student)
                    teams.append(female_team)
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

            if is_team_sport(sport_type.name):
                sport_teams = [t for t in teams if t.sport_type_id == sport_type.id]
                for team in sport_teams:
                    competition.teams.append(team)
            competitions.append(competition)
        db.commit()

        # Create student performances with realistic results
        print("Создание результатов выступлений с раздельным подсчетом по полу...")

        for competition in competitions:
            sport_type = competition.sport_type

            if is_team_sport(sport_type.name):
                # КОМАНДНЫЕ ВИДЫ СПОРТА - разделенные по полу
                for team in competition.teams:
                    # Определяем пол команды по первому участнику
                    team_gender = team.students[0].gender.value if team.students else "М"

                    # Генерируем результат команды
                    time_result, sort_value = generate_realistic_result(
                        sport_type.name,
                        team_gender,
                        random.choice([True, False])  # Случайно хорошая или обычная команда
                    )

                    # Всем членам команды одинаковый результат
                    for student in team.students:
                        performance = StudentPerformance(
                            student_id=student.id,
                            sport_type_id=competition.sport_type_id,
                            competition_id=competition.id,
                            judge_id=random.choice(judges).id,
                            points=0,  # Будет пересчитано автоматически
                            time_result=time_result,
                            original_result=sort_value
                        )
                        db.add(performance)

            else:
                # ИНДИВИДУАЛЬНЫЕ ВИДЫ СПОРТА - обеспечиваем участие обоих полов
                male_participants = []
                female_participants = []

                for faculty in faculties:
                    faculty_students = [s for s in students if s.group.faculty_id == faculty.id]
                    male_students = [s for s in faculty_students if s.gender.value == "М"]
                    female_students = [s for s in faculty_students if s.gender.value == "Ж"]

                    # Выбираем 2-3 мужчин и 2-3 женщин от каждого факультета
                    male_count = random.randint(2, min(3, len(male_students)))
                    female_count = random.randint(2, min(3, len(female_students)))

                    male_participants.extend(random.sample(male_students, male_count))
                    female_participants.extend(random.sample(female_students, female_count))

                # Создаем выступления для мужчин
                for student in male_participants:
                    is_good_athlete = random.random() < 0.3  # 30% шанс быть хорошим спортсменом

                    time_result, sort_value = generate_realistic_result(
                        sport_type.name,
                        student.gender.value,
                        is_good_athlete
                    )

                    performance = StudentPerformance(
                        student_id=student.id,
                        sport_type_id=competition.sport_type_id,
                        competition_id=competition.id,
                        judge_id=random.choice(judges).id,
                        points=0,  # Будет пересчитано автоматически
                        time_result=time_result,
                        original_result=sort_value
                    )
                    db.add(performance)

                # Создаем выступления для женщин
                for student in female_participants:
                    is_good_athlete = random.random() < 0.3  # 30% шанс быть хорошим спортсменом

                    time_result, sort_value = generate_realistic_result(
                        sport_type.name,
                        student.gender.value,
                        is_good_athlete
                    )

                    performance = StudentPerformance(
                        student_id=student.id,
                        sport_type_id=competition.sport_type_id,
                        competition_id=competition.id,
                        judge_id=random.choice(judges).id,
                        points=0,  # Будет пересчитано автоматически
                        time_result=time_result,
                        original_result=sort_value
                    )
                    db.add(performance)

        db.commit()

        # Теперь пересчитываем баллы согласно местам с раздельным подсчетом по полу
        print("Пересчет баллов с раздельным подсчетом по полу...")
        from ..api.results import recalculate_competition_points, update_faculty_results_all

        for sport_type in sport_types:
            recalculate_competition_points(db, sport_type.id)

        # Обновляем результаты факультетов
        update_faculty_results_all(db)

        print("База данных успешно заполнена с раздельным подсчетом баллов по полу!")
        print(f"Создано:")
        print(f"  - Факультетов: {len(faculties)}")
        print(f"  - Групп: {len(groups)}")
        print(f"  - Студентов: {len(students)} (по {len(students) // 2} мужчин и женщин)")
        print(f"  - Видов спорта: {len(sport_types)}")
        print(f"  - Команд: {len(teams)}")
        print(f"  - Соревнований: {len(competitions)}")
        print(f"  - Выступлений: {db.query(StudentPerformance).count()}")

        # Показываем примеры баллов
        print("\nСистема начисления баллов (раздельно для каждого пола):")
        print("  МУЖЧИНЫ:")
        for i in range(1, 4):
            print(f"    {i} место = {get_points_for_place(i)} баллов")
        print("  ЖЕНЩИНЫ:")
        for i in range(1, 4):
            print(f"    {i} место = {get_points_for_place(i)} баллов")
        print(f"  11+ места (любой пол) = {get_points_for_place(11)} балл")

    except Exception as e:
        print(f"Ошибка при заполнении базы данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_database()