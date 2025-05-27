from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from ..database import Base

team_students = Table('team_students', Base.metadata,
                      Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True),
                      Column('student_id', Integer, ForeignKey('students.id'), primary_key=True)
                      )


class SportType(Base):
    __tablename__ = "sport_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    judges = relationship("Judge", back_populates="sport_type")
    teams = relationship("Team", back_populates="sport_type")
    competitions = relationship("Competition", back_populates="sport_type")
    performances = relationship("StudentPerformance", back_populates="sport_type")
    faculty_results = relationship("FacultyCompetitionResult", back_populates="sport_type")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    sport_type_id = Column(Integer, ForeignKey("sport_types.id"))
    faculty_id = Column(Integer, ForeignKey("faculties.id"))

    sport_type = relationship("SportType", back_populates="teams")
    faculty = relationship("Faculty")
    students = relationship("Student", secondary=team_students, back_populates="teams")
    competitions = relationship("Competition", secondary="competition_teams", back_populates="teams")