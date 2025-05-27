from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from ..database import Base


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    abbreviation = Column(String, unique=True, nullable=False)


    groups = relationship("Group", back_populates="faculty")
    teachers = relationship("Teacher", back_populates="faculty")
    competition_results = relationship("FacultyCompetitionResult", back_populates="faculty")
    total_points = relationship("FacultyTotalPoints", back_populates="faculty", uselist=False)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id"))

    faculty = relationship("Faculty", back_populates="groups")
    students = relationship("Student", back_populates="group")
    teachers = relationship("Teacher", back_populates="group")