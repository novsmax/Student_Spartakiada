# backend/app/main.py - ПОЛНАЯ ВЕРСИЯ
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api import auth, users, students, competitions, results
from .database import engine, Base
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Spartakiada API",
    version="1.0.0",
    description="API для управления студенческой спартакиадой",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(competitions.router, prefix="/api/competitions", tags=["competitions"])
app.include_router(results.router, prefix="/api/results", tags=["results"])

# Обработчик глобальных ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )

# Корневой endpoint
@app.get("/")
def read_root():
    """Корневой endpoint API"""
    return {
        "message": "Welcome to Spartakiada API",
        "version": "1.0.0",
        "documentation": "/docs",
        "alternative_docs": "/redoc"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """Проверка состояния сервиса"""
    try:
        # Можно добавить проверку подключения к БД
        return {
            "status": "healthy",
            "version": "1.0.0",
            "service": "Spartakiada API"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# API информация
@app.get("/api/info")
def api_info():
    """Информация об API"""
    return {
        "title": "Spartakiada API",
        "version": "1.0.0",
        "description": "API для управления студенческой спартакиадой",
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users", 
            "students": "/api/students",
            "competitions": "/api/competitions",
            "results": "/api/results"
        },
        "features": [
            "Управление пользователями",
            "Регистрация студентов",
            "Создание соревнований",
            "Ведение результатов",
            "Подсчет рейтингов",
            "Раздельный подсчет по полу"
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Spartakiada API starting up...")
    logger.info("Database tables created successfully")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Spartakiada API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )