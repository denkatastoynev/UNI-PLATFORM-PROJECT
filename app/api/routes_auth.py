from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_role_names,
    hash_password,
    require_roles,
)

router = APIRouter()


class RoleRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=3)
    role_names: List[str]
    staff_id: Optional[int] = None
    student_id: Optional[int] = None
    is_active: bool = True


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool
    staff_id: Optional[int] = None
    student_id: Optional[int] = None
    roles: List[RoleRead]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    roles: List[str]


@router.post("/login", response_model=TokenResponse, summary="Вход в системата")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидно потребителско име или парола.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_names = get_role_names(user)
    access_token = create_access_token(subject=user.username, roles=role_names)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        roles=role_names,
    )


@router.get("/me", response_model=UserRead, summary="Текущ потребител")
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post(
    "/seed",
    summary="Създаване на начални роли и admin",
)
def seed_roles_and_admin(db: Session = Depends(get_db)):
    existing_users_count = db.query(models.User).count()
    if existing_users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed е позволен само при празна система.",
        )

    role_map = {
        "admin": "Пълен административен достъп",
        "secretary": "Управление на учебни и административни данни",
        "teacher": "Работа с оценки, протоколи и справки",
        "student": "Достъп до собствен профил и оценки",
    }

    for role_name, description in role_map.items():
        role = db.query(models.Role).filter_by(name=role_name).first()
        if not role:
            db.add(models.Role(name=role_name, description=description))

    db.commit()

    admin_role = db.query(models.Role).filter_by(name="admin").first()
    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Неуспешно създаване на admin роля.",
        )

    admin_user = models.User(
        username="admin",
        password_hash=hash_password("admin123"),
        is_active=True,
    )
    admin_user.roles.append(admin_role)

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "message": "Началните роли и admin потребителят са създадени успешно.",
        "default_admin_credentials": {
            "username": "admin",
            "password": "admin123",
        },
    }


@router.post(
    "/users",
    response_model=UserRead,
    summary="Създаване на потребител",
    dependencies=[Depends(require_roles("admin"))],
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    username = payload.username.strip()

    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Потребителското име не може да бъде празно.",
        )

    if not payload.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Паролата не може да бъде празна.",
        )

    if not payload.role_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Трябва да бъде подадена поне една роля.",
        )

    existing = db.query(models.User).filter_by(username=username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вече съществува потребител с това username.",
        )

    roles = db.query(models.Role).filter(models.Role.name.in_(payload.role_names)).all()
    found_role_names = {role.name for role in roles}
    missing_roles = [role for role in payload.role_names if role not in found_role_names]
    if missing_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Липсващи роли: {', '.join(missing_roles)}",
        )

    if payload.staff_id is not None:
        staff = db.query(models.Staff).filter_by(id=payload.staff_id).first()
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерен служител с посочения идентификатор.",
            )

        existing_staff_user = db.query(models.User).filter_by(staff_id=payload.staff_id).first()
        if existing_staff_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Този служител вече има потребителски акаунт.",
            )

    if payload.student_id is not None:
        student = db.query(models.Student).filter_by(id=payload.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Няма намерен студент с посочения идентификатор.",
            )

        existing_student_user = db.query(models.User).filter_by(student_id=payload.student_id).first()
        if existing_student_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Този студент вече има потребителски акаунт.",
            )

    if payload.staff_id is not None and payload.student_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Потребителят не може едновременно да е свързан и със служител, и със студент.",
        )

    user = models.User(
        username=username,
        password_hash=hash_password(payload.password),
        is_active=payload.is_active,
        staff_id=payload.staff_id,
        student_id=payload.student_id,
    )
    user.roles = roles

    db.add(user)
    db.commit()
    db.refresh(user)

    return user