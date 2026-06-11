from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles


class EnrollmentCreate(BaseModel):
    student_id: int
    course_instance_id: int
    status: Optional[str] = None


class EnrollmentRead(BaseModel):
    id: int
    student_id: int
    course_instance_id: int
    status: Optional[str] = None
    student_faculty_number: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    academic_year: Optional[str] = None

    class Config:
        orm_mode = True


router = APIRouter()


@router.get("/", response_model=List[EnrollmentRead], summary="Списък записвания")
def list_enrollments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    enrollments = db.query(models.Enrollment).all()
    result: List[EnrollmentRead] = []

    for e in enrollments:
        ci = e.course_instance
        course = ci.course if ci else None

        result.append(
            EnrollmentRead(
                id=e.id,
                student_id=e.student_id,
                course_instance_id=e.course_instance_id,
                status=e.status,
                student_faculty_number=e.student.faculty_number if e.student else None,
                course_code=course.code if course else None,
                course_name=course.name if course else None,
                academic_year=ci.academic_year if ci else None,
            )
        )

    return result


@router.get("/{enrollment_id}", response_model=EnrollmentRead, summary="Детайли за записване")
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    enrollment = db.query(models.Enrollment).filter_by(id=enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерено записване с посочения идентификатор.",
        )

    ci = enrollment.course_instance
    course = ci.course if ci else None

    return EnrollmentRead(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_instance_id=enrollment.course_instance_id,
        status=enrollment.status,
        student_faculty_number=enrollment.student.faculty_number if enrollment.student else None,
        course_code=course.code if course else None,
        course_name=course.name if course else None,
        academic_year=ci.academic_year if ci else None,
    )


@router.post("/", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED, summary="Създаване на записване")
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    student = db.query(models.Student).filter_by(id=payload.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерен студент с посочения идентификатор.",
        )

    ci = db.query(models.CourseInstance).filter_by(id=payload.course_instance_id).first()
    if not ci:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерено провеждане на дисциплина с посочения идентификатор.",
        )

    enrollment = models.Enrollment(
        student=student,
        course_instance=ci,
        status=payload.status.strip() if payload.status else None,
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    course = ci.course

    return EnrollmentRead(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_instance_id=enrollment.course_instance_id,
        status=enrollment.status,
        student_faculty_number=student.faculty_number,
        course_code=course.code if course else None,
        course_name=course.name if course else None,
        academic_year=ci.academic_year,
    )


@router.put("/{enrollment_id}", response_model=EnrollmentRead, summary="Редакция на записване")
def update_enrollment(
    enrollment_id: int,
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    enrollment = db.query(models.Enrollment).filter_by(id=enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерено записване с посочения идентификатор.",
        )

    student = db.query(models.Student).filter_by(id=payload.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерен студент с посочения идентификатор.",
        )

    ci = db.query(models.CourseInstance).filter_by(id=payload.course_instance_id).first()
    if not ci:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Няма намерено провеждане на дисциплина с посочения идентификатор.",
        )

    enrollment.student = student
    enrollment.course_instance = ci
    enrollment.status = payload.status.strip() if payload.status else None

    db.commit()
    db.refresh(enrollment)

    course = ci.course

    return EnrollmentRead(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_instance_id=enrollment.course_instance_id,
        status=enrollment.status,
        student_faculty_number=student.faculty_number,
        course_code=course.code if course else None,
        course_name=course.name if course else None,
        academic_year=ci.academic_year,
    )


@router.delete("/{enrollment_id}", summary="Изтриване на записване")
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    enrollment = db.query(models.Enrollment).filter_by(id=enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерено записване с посочения идентификатор.",
        )

    db.delete(enrollment)
    db.commit()

    return {"message": "Записването беше изтрито успешно."}