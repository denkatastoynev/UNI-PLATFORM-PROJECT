from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles


class CourseInstanceCreate(BaseModel):
    academic_year: str
    term: Optional[str] = None
    group: Optional[str] = None
    course_id: int


class CourseInstanceRead(BaseModel):
    id: int
    academic_year: str
    term: Optional[str] = None
    group: Optional[str] = None
    course_id: int
    course_code: Optional[str] = None
    course_name: Optional[str] = None

    class Config:
        orm_mode = True


router = APIRouter()


@router.get("/", response_model=List[CourseInstanceRead], summary="Списък провеждания на дисциплини")
def list_course_instances(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    instances = db.query(models.CourseInstance).order_by(models.CourseInstance.academic_year).all()
    result: List[CourseInstanceRead] = []

    for ci in instances:
        result.append(
            CourseInstanceRead(
                id=ci.id,
                academic_year=ci.academic_year,
                term=ci.term,
                group=ci.group,
                course_id=ci.course_id,
                course_code=ci.course.code if ci.course else None,
                course_name=ci.course.name if ci.course else None,
            )
        )

    return result


@router.get("/{course_instance_id}", response_model=CourseInstanceRead, summary="Детайли за провеждане на дисциплина")
def get_course_instance(
    course_instance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    instance = db.query(models.CourseInstance).filter_by(id=course_instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерено провеждане на дисциплина с посочения идентификатор.",
        )

    return CourseInstanceRead(
        id=instance.id,
        academic_year=instance.academic_year,
        term=instance.term,
        group=instance.group,
        course_id=instance.course_id,
        course_code=instance.course.code if instance.course else None,
        course_name=instance.course.name if instance.course else None,
    )


@router.post("/", response_model=CourseInstanceRead, status_code=status.HTTP_201_CREATED, summary="Създаване на провеждане на дисциплина")
def create_course_instance(
    payload: CourseInstanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    academic_year = payload.academic_year.strip()

    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Учебната година не може да бъде празна.",
        )

    course = db.query(models.Course).filter_by(id=payload.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерена дисциплина с посочения идентификатор.",
        )

    instance = models.CourseInstance(
        academic_year=academic_year,
        term=payload.term.strip() if payload.term else None,
        group=payload.group.strip() if payload.group else None,
        course=course,
    )

    db.add(instance)
    db.commit()
    db.refresh(instance)

    return CourseInstanceRead(
        id=instance.id,
        academic_year=instance.academic_year,
        term=instance.term,
        group=instance.group,
        course_id=instance.course_id,
        course_code=instance.course.code if instance.course else None,
        course_name=instance.course.name if instance.course else None,
    )


@router.put("/{course_instance_id}", response_model=CourseInstanceRead, summary="Редакция на провеждане на дисциплина")
def update_course_instance(
    course_instance_id: int,
    payload: CourseInstanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    instance = db.query(models.CourseInstance).filter_by(id=course_instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерено провеждане на дисциплина с посочения идентификатор.",
        )

    academic_year = payload.academic_year.strip()
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Учебната година не може да бъде празна.",
        )

    course = db.query(models.Course).filter_by(id=payload.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерена дисциплина с посочения идентификатор.",
        )

    instance.academic_year = academic_year
    instance.term = payload.term.strip() if payload.term else None
    instance.group = payload.group.strip() if payload.group else None
    instance.course = course

    db.commit()
    db.refresh(instance)

    return CourseInstanceRead(
        id=instance.id,
        academic_year=instance.academic_year,
        term=instance.term,
        group=instance.group,
        course_id=instance.course_id,
        course_code=instance.course.code if instance.course else None,
        course_name=instance.course.name if instance.course else None,
    )


@router.delete("/{course_instance_id}", summary="Изтриване на провеждане на дисциплина")
def delete_course_instance(
    course_instance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    instance = db.query(models.CourseInstance).filter_by(id=course_instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерено провеждане на дисциплина с посочения идентификатор.",
        )

    db.delete(instance)
    db.commit()

    return {"message": "Провеждането на дисциплината беше изтрито успешно."}