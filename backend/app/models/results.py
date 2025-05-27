from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint, String, Table
from sqlalchemy.orm import relationship
from ..database import Base


class StudentPerformance(Base):
    __tablename__ = "student_performances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    sport_type_id = Column(Integer, ForeignKey("sport_types.id"))
    competition_id = Column(Integer, ForeignKey("competitions.id"))
    judge_id = Column(Integer, ForeignKey("judges.id"))
    points = Column(Float, nullable=False)
    time_result = Column(String)  # For time-based results like "1:36:45"

    # Relationships
    student = relationship("Student", back_populates="performances")
    sport_type = relationship("SportType", back_populates="performances")
    competition = relationship("Competition", back_populates="performances")
    judge = relationship("Judge", back_populates="performances")
    faculty_result = relationship("FacultyCompetitionResult", secondary="faculty_result_performances")

    __table_args__ = (
        UniqueConstraint('student_id', 'competition_id', name='_student_competition_uc'),
    )


# Association table for many-to-many relationship between faculty results and performances
faculty_result_performances = Table('faculty_result_performances', Base.metadata,
                                    Column('faculty_result_id', Integer, ForeignKey('faculty_competition_results.id'),
                                           primary_key=True),
                                    Column('performance_id', Integer, ForeignKey('student_performances.id'),
                                           primary_key=True)
                                    )


class FacultyCompetitionResult(Base):
    __tablename__ = "faculty_competition_results"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    sport_type_id = Column(Integer, ForeignKey("sport_types.id"))
    total_points = Column(Float, nullable=False)
    place = Column(Integer)

    faculty = relationship("Faculty", back_populates="competition_results")
    sport_type = relationship("SportType", back_populates="faculty_results")
    performances = relationship("StudentPerformance", secondary=faculty_result_performances)
    total_points_rel = relationship("FacultyTotalPoints", secondary="total_points_results")

    __table_args__ = (
        UniqueConstraint('faculty_id', 'sport_type_id', name='_faculty_sport_uc'),
    )


total_points_results = Table('total_points_results', Base.metadata,
                             Column('total_points_id', Integer, ForeignKey('faculty_total_points.id'),
                                    primary_key=True),
                             Column('faculty_result_id', Integer, ForeignKey('faculty_competition_results.id'),
                                    primary_key=True)
                             )


class FacultyTotalPoints(Base):
    __tablename__ = "faculty_total_points"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), unique=True)
    total_points = Column(Float, nullable=False)
    overall_place = Column(Integer)

    # Relationships
    faculty = relationship("Faculty", back_populates="total_points")
    competition_results = relationship("FacultyCompetitionResult", secondary=total_points_results)