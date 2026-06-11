from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles


class StudentCreate(BaseModel):
    faculty_number: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    admission_year: Optional[int] = None
    study_form: Optional[str] = None
    programme_code: Optional[str] = None


class StudentRead(BaseModel):
    id: int
    faculty_number: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    admission_year: Optional[int] = None
    study_form: Optional[str] = None
    programme_code: Optional[str] = None

    class Config:
        orm_mode = True


router = APIRouter()


@router.get("/", response_model=List[StudentRead], summary="Списък студенти")
def list_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    students = db.query(models.Student).order_by(models.Student.id.desc()).all()
    result: List[StudentRead] = []

    for s in students:
        result.append(
            StudentRead(
                id=s.id,
                faculty_number=s.faculty_number,
                first_name=s.first_name,
                last_name=s.last_name,
                email=s.email,
                admission_year=s.admission_year,
                study_form=s.study_form,
                programme_code=s.programme.code if s.programme else None,
            )
        )

    return result


@router.get("/{student_id}", response_model=StudentRead, summary="Детайли за студент")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    student = db.query(models.Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерен студент с посочения идентификатор.",
        )

    return StudentRead(
        id=student.id,
        faculty_number=student.faculty_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        admission_year=student.admission_year,
        study_form=student.study_form,
        programme_code=student.programme.code if student.programme else None,
    )


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED, summary="Създаване на студент")
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    faculty_number = payload.faculty_number.strip()
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()

    if not faculty_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Факултетният номер не може да бъде празен.",
        )

    if not first_name or not last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Името и фамилията не могат да бъдат празни.",
        )

    existing = db.query(models.Student).filter_by(faculty_number=faculty_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува студент с този факултетен номер.",
        )

    programme = None
    if payload.programme_code:
        programme = db.query(models.Programme).filter_by(code=payload.programme_code.strip()).first()
        if not programme:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерена специалност с посочения код.",
            )

    student = models.Student(
        faculty_number=faculty_number,
        first_name=first_name,
        last_name=last_name,
        email=payload.email,
        admission_year=payload.admission_year,
        study_form=payload.study_form.strip() if payload.study_form else None,
        programme=programme,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return StudentRead(
        id=student.id,
        faculty_number=student.faculty_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        admission_year=student.admission_year,
        study_form=student.study_form,
        programme_code=student.programme.code if student.programme else None,
    )


@router.put("/{student_id}", response_model=StudentRead, summary="Редакция на студент")
def update_student(
    student_id: int,
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    student = db.query(models.Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерен студент с посочения идентификатор.",
        )

    faculty_number = payload.faculty_number.strip()
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()

    if not faculty_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Факултетният номер не може да бъде празен.",
        )

    if not first_name or not last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Името и фамилията не могат да бъдат празни.",
        )

    existing = db.query(models.Student).filter(
        models.Student.faculty_number == faculty_number,
        models.Student.id != student_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува друг студент с този факултетен номер.",
        )

    programme = None
    if payload.programme_code:
        programme = db.query(models.Programme).filter_by(code=payload.programme_code.strip()).first()
        if not programme:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерена специалност с посочения код.",
            )

    student.faculty_number = faculty_number
    student.first_name = first_name
    student.last_name = last_name
    student.email = payload.email
    student.admission_year = payload.admission_year
    student.study_form = payload.study_form.strip() if payload.study_form else None
    student.programme = programme

    db.commit()
    db.refresh(student)

    return StudentRead(
        id=student.id,
        faculty_number=student.faculty_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        admission_year=student.admission_year,
        study_form=student.study_form,
        programme_code=student.programme.code if student.programme else None,
    )


@router.delete("/{student_id}", summary="Изтриване на студент")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    student = db.query(models.Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерен студент с посочения идентификатор.",
        )

    db.delete(student)
    db.commit()

    return {"message": "Студентът беше изтрит успешно."}