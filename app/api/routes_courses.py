from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles


class CourseCreate(BaseModel):
    code: str
    name: str
    semester: Optional[int] = None
    mandatory_type: Optional[str] = None
    credits: Optional[int] = None
    hours_lectures: Optional[int] = None
    hours_exercises: Optional[int] = None
    programme_code: Optional[str] = None


class CourseRead(BaseModel):
    id: int
    code: str
    name: str
    semester: Optional[int] = None
    mandatory_type: Optional[str] = None
    credits: Optional[int] = None
    hours_lectures: Optional[int] = None
    hours_exercises: Optional[int] = None
    programme_code: Optional[str] = None

    class Config:
        orm_mode = True


router = APIRouter()


@router.get("/", response_model=List[CourseRead], summary="Списък дисциплини")
def list_courses(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    courses = db.query(models.Course).order_by(models.Course.code).all()
    result: List[CourseRead] = []

    for c in courses:
        result.append(
            CourseRead(
                id=c.id,
                code=c.code,
                name=c.name,
                semester=c.semester,
                mandatory_type=c.mandatory_type,
                credits=c.credits,
                hours_lectures=c.hours_lectures,
                hours_exercises=c.hours_exercises,
                programme_code=c.programme.code if c.programme else None,
            )
        )

    return result


@router.get("/{course_id}", response_model=CourseRead, summary="Детайли за дисциплина")
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    course = db.query(models.Course).filter_by(id=course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена дисциплина с посочения идентификатор.",
        )

    return CourseRead(
        id=course.id,
        code=course.code,
        name=course.name,
        semester=course.semester,
        mandatory_type=course.mandatory_type,
        credits=course.credits,
        hours_lectures=course.hours_lectures,
        hours_exercises=course.hours_exercises,
        programme_code=course.programme.code if course.programme else None,
    )


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED, summary="Създаване на дисциплина")
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    code = payload.code.strip()
    name = payload.name.strip()

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Кодът на дисциплината не може да бъде празен.",
        )

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Името на дисциплината не може да бъде празно.",
        )

    existing = db.query(models.Course).filter_by(code=code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува дисциплина с този код.",
        )

    programme = None
    if payload.programme_code:
        programme = db.query(models.Programme).filter_by(code=payload.programme_code.strip()).first()
        if not programme:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерена специалност с посочения код.",
            )

    course = models.Course(
        code=code,
        name=name,
        semester=payload.semester,
        mandatory_type=payload.mandatory_type.strip() if payload.mandatory_type else None,
        credits=payload.credits,
        hours_lectures=payload.hours_lectures,
        hours_exercises=payload.hours_exercises,
        programme=programme,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return CourseRead(
        id=course.id,
        code=course.code,
        name=course.name,
        semester=course.semester,
        mandatory_type=course.mandatory_type,
        credits=course.credits,
        hours_lectures=course.hours_lectures,
        hours_exercises=course.hours_exercises,
        programme_code=course.programme.code if course.programme else None,
    )


@router.put("/{course_id}", response_model=CourseRead, summary="Редакция на дисциплина")
def update_course(
    course_id: int,
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    course = db.query(models.Course).filter_by(id=course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена дисциплина с посочения идентификатор.",
        )

    code = payload.code.strip()
    name = payload.name.strip()

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Кодът на дисциплината не може да бъде празен.",
        )

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Името на дисциплината не може да бъде празно.",
        )

    existing = db.query(models.Course).filter(
        models.Course.code == code,
        models.Course.id != course_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува друга дисциплина с този код.",
        )

    programme = None
    if payload.programme_code:
        programme = db.query(models.Programme).filter_by(code=payload.programme_code.strip()).first()
        if not programme:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерена специалност с посочения код.",
            )

    course.code = code
    course.name = name
    course.semester = payload.semester
    course.mandatory_type = payload.mandatory_type.strip() if payload.mandatory_type else None
    course.credits = payload.credits
    course.hours_lectures = payload.hours_lectures
    course.hours_exercises = payload.hours_exercises
    course.programme = programme

    db.commit()
    db.refresh(course)

    return CourseRead(
        id=course.id,
        code=course.code,
        name=course.name,
        semester=course.semester,
        mandatory_type=course.mandatory_type,
        credits=course.credits,
        hours_lectures=course.hours_lectures,
        hours_exercises=course.hours_exercises,
        programme_code=course.programme.code if course.programme else None,
    )


@router.delete("/{course_id}", summary="Изтриване на дисциплина")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    course = db.query(models.Course).filter_by(id=course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена дисциплина с посочения идентификатор.",
        )

    db.delete(course)
    db.commit()

    return {"message": "Дисциплината беше изтрита успешно."}