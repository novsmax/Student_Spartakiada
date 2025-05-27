from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, users, students, competitions, results
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spartakiada API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(competitions.router, prefix="/api/competitions", tags=["competitions"])
app.include_router(results.router, prefix="/api/results", tags=["results"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Spartakiada API"}