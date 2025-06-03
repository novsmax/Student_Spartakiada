# backend/app/schemas/__init__.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from .user import UserCreate, UserRead, UserLogin, Token
from .student import StudentCreate, StudentRead, StudentFindOrCreateRequest, StudentFindOrCreateResponse
from .faculty import FacultyCreate, FacultyRead, GroupCreate, GroupRead
from .sport import SportTypeCreate, SportTypeRead, TeamCreate, TeamRead
from .competition import CompetitionCreate, CompetitionRead
from .results import (
    StudentPerformanceCreate, StudentPerformanceRead, StudentPerformanceUpdate,
    FacultyCompetitionResultRead, FacultyTotalPointsRead,
    CompetitionResultsFilter, StudentPerformanceDetail
)