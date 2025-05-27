from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

competition_teams = Table('competition_teams', Base.metadata,
                          Column('competition_id', Integer, ForeignKey('competitions.id'), primary_key=True),
                          Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True)
                          )


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sport_type_id = Column(Integer, ForeignKey("sport_types.id"))
    date = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)

    sport_type = relationship("SportType", back_populates="competitions")
    teams = relationship("Team", secondary=competition_teams, back_populates="competitions")
    performances = relationship("StudentPerformance", back_populates="competition")