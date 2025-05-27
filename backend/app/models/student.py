from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class Gender(str, enum.Enum):
    MALE = "М"
    FEMALE = "Ж"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String)
    gender = Column(Enum(Gender), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))

    group = relationship("Group", back_populates="students")
    teams = relationship("Team", secondary="team_students", back_populates="students")
    performances = relationship("StudentPerformance", back_populates="student")