from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_health,
    routes_programmes,
    routes_students,
    routes_courses,
    routes_course_instances,
    routes_enrollments,
    routes_grades,
    routes_reports,
    routes_protocols,
    routes_auth,
    routes_ai_agent,
)

app = FastAPI(title="University Admin AIS with AI Agent")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router, prefix="/api/health", tags=["health"])
app.include_router(routes_programmes.router, prefix="/api/programmes", tags=["programmes"])
app.include_router(routes_students.router, prefix="/api/students", tags=["students"])
app.include_router(routes_courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(routes_course_instances.router, prefix="/api/course-instances", tags=["course_instances"])
app.include_router(routes_enrollments.router, prefix="/api/enrollments", tags=["enrollments"])
app.include_router(routes_grades.router, prefix="/api/grades", tags=["grades"])
app.include_router(routes_reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(routes_protocols.router, prefix="/api/protocols", tags=["protocols"])
app.include_router(routes_auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(routes_ai_agent.router, prefix="/api/ai-agent", tags=["ai_agent"])


@app.get("/")
async def root():
    return {"message": "University Admin AIS prototype is running"}