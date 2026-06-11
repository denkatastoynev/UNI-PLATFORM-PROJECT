from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles


class GradeCreate(BaseModel):
    protocol_entry_id: Optional[int] = None
    enrollment_id: int
    academic_year: str
    exam_date: Optional[date] = None
    grade_numeric: Optional[int] = None
    grade_text_bg: Optional[str] = None
    grade_ects: Optional[str] = None
    is_transferred: Optional[bool] = False


class GradeRead(BaseModel):
    id: int
    protocol_entry_id: Optional[int] = None
    enrollment_id: int
    academic_year: str
    exam_date: Optional[date] = None
    grade_numeric: Optional[int] = None
    grade_text_bg: Optional[str] = None
    grade_ects: Optional[str] = None
    is_transferred: Optional[bool] = False

    class Config:
        orm_mode = True


router = APIRouter()


@router.get("/", response_model=List[GradeRead], summary="Списък оценки")
def list_grades(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    grades = db.query(models.Grade).order_by(models.Grade.id.desc()).all()
    result: List[GradeRead] = []

    for g in grades:
        result.append(
            GradeRead(
                id=g.id,
                protocol_entry_id=g.protocol_entry_id,
                enrollment_id=g.enrollment_id,
                academic_year=g.academic_year,
                exam_date=g.exam_date,
                grade_numeric=g.grade_numeric,
                grade_text_bg=g.grade_text_bg,
                grade_ects=g.grade_ects,
                is_transferred=g.is_transferred,
            )
        )

    return result


@router.get("/{grade_id}", response_model=GradeRead, summary="Детайли за оценка")
def get_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    grade = db.query(models.Grade).filter_by(id=grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена оценка с посочения идентификатор.",
        )

    return GradeRead(
        id=grade.id,
        protocol_entry_id=grade.protocol_entry_id,
        enrollment_id=grade.enrollment_id,
        academic_year=grade.academic_year,
        exam_date=grade.exam_date,
        grade_numeric=grade.grade_numeric,
        grade_text_bg=grade.grade_text_bg,
        grade_ects=grade.grade_ects,
        is_transferred=grade.is_transferred,
    )


@router.post("/", response_model=GradeRead, status_code=status.HTTP_201_CREATED, summary="Създаване на оценка")
def create_grade(
    payload: GradeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    academic_year = payload.academic_year.strip()
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Учебната година не може да бъде празна.",
        )

    enrollment = db.query(models.Enrollment).filter_by(id=payload.enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерено записване с посочения идентификатор.",
        )

    if payload.protocol_entry_id is not None:
        protocol_entry = db.query(models.ProtocolEntry).filter_by(id=payload.protocol_entry_id).first()
        if not protocol_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерен ред в протокол с посочения идентификатор.",
            )
    else:
        protocol_entry = None

    if payload.grade_numeric is not None and payload.grade_numeric not in [2, 3, 4, 5, 6]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Числовата оценка трябва да бъде цяло число от 2 до 6.",
        )

    grade = models.Grade(
        protocol_entry=protocol_entry,
        enrollment=enrollment,
        academic_year=academic_year,
        exam_date=payload.exam_date,
        grade_numeric=payload.grade_numeric,
        grade_text_bg=payload.grade_text_bg.strip() if payload.grade_text_bg else None,
        grade_ects=payload.grade_ects.strip() if payload.grade_ects else None,
        is_transferred=payload.is_transferred or False,
    )

    db.add(grade)
    db.commit()
    db.refresh(grade)

    return GradeRead(
        id=grade.id,
        protocol_entry_id=grade.protocol_entry_id,
        enrollment_id=grade.enrollment_id,
        academic_year=grade.academic_year,
        exam_date=grade.exam_date,
        grade_numeric=grade.grade_numeric,
        grade_text_bg=grade.grade_text_bg,
        grade_ects=grade.grade_ects,
        is_transferred=grade.is_transferred,
    )


@router.put("/{grade_id}", response_model=GradeRead, summary="Редакция на оценка")
def update_grade(
    grade_id: int,
    payload: GradeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    grade = db.query(models.Grade).filter_by(id=grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена оценка с посочения идентификатор.",
        )

    academic_year = payload.academic_year.strip()
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Учебната година не може да бъде празна.",
        )

    enrollment = db.query(models.Enrollment).filter_by(id=payload.enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерено записване с посочения идентификатор.",
        )

    if payload.protocol_entry_id is not None:
        protocol_entry = db.query(models.ProtocolEntry).filter_by(id=payload.protocol_entry_id).first()
        if not protocol_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерен ред в протокол с посочения идентификатор.",
            )
    else:
        protocol_entry = None

    if payload.grade_numeric is not None and payload.grade_numeric not in [2, 3, 4, 5, 6]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Числовата оценка трябва да бъде цяло число от 2 до 6.",
        )

    grade.protocol_entry = protocol_entry
    grade.enrollment = enrollment
    grade.academic_year = academic_year
    grade.exam_date = payload.exam_date
    grade.grade_numeric = payload.grade_numeric
    grade.grade_text_bg = payload.grade_text_bg.strip() if payload.grade_text_bg else None
    grade.grade_ects = payload.grade_ects.strip() if payload.grade_ects else None
    grade.is_transferred = payload.is_transferred or False

    db.commit()
    db.refresh(grade)

    return GradeRead(
        id=grade.id,
        protocol_entry_id=grade.protocol_entry_id,
        enrollment_id=grade.enrollment_id,
        academic_year=grade.academic_year,
        exam_date=grade.exam_date,
        grade_numeric=grade.grade_numeric,
        grade_text_bg=grade.grade_text_bg,
        grade_ects=grade.grade_ects,
        is_transferred=grade.is_transferred,
    )


@router.delete("/{grade_id}", summary="Изтриване на оценка")
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    grade = db.query(models.Grade).filter_by(id=grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена оценка с посочения идентификатор.",
        )

    db.delete(grade)
    db.commit()

    return {"message": "Оценката беше изтрита успешно."}