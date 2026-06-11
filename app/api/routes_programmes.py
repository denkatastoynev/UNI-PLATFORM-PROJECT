from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles


class ProgrammeCreate(BaseModel):
    code: str
    name: str
    degree: Optional[str] = None
    field: Optional[str] = None


class ProgrammeRead(BaseModel):
    id: int
    code: str
    name: str
    degree: Optional[str] = None
    field: Optional[str] = None

    class Config:
        orm_mode = True


router = APIRouter()


@router.get("/", response_model=List[ProgrammeRead], summary="Списък специалности")
def list_programmes(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    programmes = db.query(models.Programme).order_by(models.Programme.code).all()
    return programmes


@router.get("/{programme_id}", response_model=ProgrammeRead, summary="Детайли за специалност")
def get_programme(
    programme_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    programme = db.query(models.Programme).filter_by(id=programme_id).first()
    if not programme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена специалност с посочения идентификатор.",
        )

    return programme


@router.post("/", response_model=ProgrammeRead, status_code=status.HTTP_201_CREATED, summary="Създаване на специалност")
def create_programme(
    payload: ProgrammeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    code = payload.code.strip()
    name = payload.name.strip()

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Кодът на специалността не може да бъде празен.",
        )

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Името на специалността не може да бъде празно.",
        )

    existing = db.query(models.Programme).filter_by(code=code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува специалност с този код.",
        )

    programme = models.Programme(
        code=code,
        name=name,
        degree=payload.degree.strip() if payload.degree else None,
        field=payload.field.strip() if payload.field else None,
    )

    db.add(programme)
    db.commit()
    db.refresh(programme)

    return programme


@router.put("/{programme_id}", response_model=ProgrammeRead, summary="Редакция на специалност")
def update_programme(
    programme_id: int,
    payload: ProgrammeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    programme = db.query(models.Programme).filter_by(id=programme_id).first()
    if not programme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена специалност с посочения идентификатор.",
        )

    code = payload.code.strip()
    name = payload.name.strip()

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Кодът на специалността не може да бъде празен.",
        )

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Името на специалността не може да бъде празно.",
        )

    existing = db.query(models.Programme).filter(
        models.Programme.code == code,
        models.Programme.id != programme_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува друга специалност с този код.",
        )

    programme.code = code
    programme.name = name
    programme.degree = payload.degree.strip() if payload.degree else None
    programme.field = payload.field.strip() if payload.field else None

    db.commit()
    db.refresh(programme)

    return programme


@router.delete("/{programme_id}", summary="Изтриване на специалност")
def delete_programme(
    programme_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary")),
):
    programme = db.query(models.Programme).filter_by(id=programme_id).first()
    if not programme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерена специалност с посочения идентификатор.",
        )

    db.delete(programme)
    db.commit()

    return {"message": "Специалността беше изтрита успешно."}