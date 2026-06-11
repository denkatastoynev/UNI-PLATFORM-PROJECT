# app/api/routes_ai_agent.py
import json
import os
from typing import Literal, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import google.generativeai as genai

from app.db.database import get_db
from app.db import models
from app.api import routes_reports
from app.core.security import get_current_user

router = APIRouter()


class AIQuery(BaseModel):
    """
    Вход към AI административния асистент.
    """
    mode: Literal["student_profile", "student_average", "course_average"] = Field(
        ...,
        description=(
            "Тип справка: "
            "\"student_profile\" – подробен профил и справка за студент; "
            "\"student_average\" – среден успех на студент; "
            "\"course_average\" – среден успех по провеждане."
        ),
    )
    faculty_number: Optional[str] = Field(
        None,
        description="Факултетен номер – задължителен за student_profile и student_average.",
    )
    course_instance_id: Optional[int] = Field(
        None,
        description="Идентификатор на провеждане – задължителен за course_average.",
    )
    question: Optional[str] = Field(
        None,
        description="Свободен въпрос към асистента; ако липсва, се използва стандартна формулировка.",
    )


class AIAnswer(BaseModel):
    """
    Отговор от AI административния асистент.
    """
    answer: str
    data: Dict[str, Any]


def _get_gemini_model() -> genai.GenerativeModel:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не е конфигуриран ключ за достъп до Gemini (променлива GOOGLE_API_KEY).",
        )
    genai.configure(api_key=api_key)
    # Моделът може да се смени според наличния (напр. gemini-1.5-pro)
    return genai.GenerativeModel("gemini-1.5-pro")


@router.post(
    "/assistant",
    response_model=AIAnswer,
    summary="AI административен асистент (Gemini + вътрешни справки)",
)
def ai_assistant(
    payload: AIQuery,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    AI асистент, който комбинира вътрешните справки на системата с
    езиковия модел Gemini, за да генерира обяснения и обобщения.
    """

    # 1. Подготовка на структурирани данни според режима
    data: Dict[str, Any]
    default_question: str

    if payload.mode == "student_profile":
        if not payload.faculty_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="За режим student_profile е необходим факултетен номер.",
            )

        student = db.query(models.Student).filter_by(
            faculty_number=payload.faculty_number
        ).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Студентът не е намерен.",
            )

        # използваме готовата ти логика за студентски профил
        profile_dict = routes_reports.get_student_profile(student.id, db)  # type: ignore[arg-type]
        data = {
            "type": "student_profile",
            "faculty_number": payload.faculty_number,
            "profile": profile_dict,
        }
        default_question = (
            f"Направи структурирано резюме на академичния профил на студента "
            f"с факултетен номер {payload.faculty_number}."
        )

    elif payload.mode == "student_average":
        if not payload.faculty_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="За режим student_average е необходим факултетен номер.",
            )

        # използваме готовата ти справка за среден успех
        avg_report = routes_reports.get_student_average_report(
            payload.faculty_number, db
        )
        data = {
            "type": "student_average",
            "faculty_number": payload.faculty_number,
            "average_report": avg_report.dict(),
        }
        default_question = (
            f"Обясни накратко средния успех и броя оценки на студента "
            f"с факултетен номер {payload.faculty_number}."
        )

    elif payload.mode == "course_average":
        if payload.course_instance_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="За режим course_average е необходим идентификатор на провеждане.",
            )

        avg_report = routes_reports.get_course_average_report(
            payload.course_instance_id, db
        )
        data = {
            "type": "course_average",
            "course_instance_id": payload.course_instance_id,
            "average_report": avg_report.dict(),
        }
        default_question = (
            "Опиши накратко средния успех и броя оценки за това провеждане на дисциплина."
        )

    else:
        # Тук няма как да стигнем, защото mode е ограничен с Literal
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдържан режим.",
        )

    # 2. Подготовка на подсказката към модела
    user_question = payload.question or default_question

    prompt = (
        "Ти си вътрешен административен асистент на учебен отдел в университет. "
        "Получаваш структурирани данни от административната информационна система "
        "под формата на JSON. На базата на тези данни отговори на ясен, кратък и "
        "конкретен български език, без да измисляш несъществуващи стойности.\n\n"
        "Ако в данните липсва дадена информация, изрично отбележи, че не е налична.\n\n"
        "Структурирани данни:\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
        f"Въпрос на потребителя: {user_question}\n\n"
        "Отговори под формата на кратко текстово обобщение, подходящо за служител "
        "в учебен отдел или ръководство."
    )

    try:
        model = _get_gemini_model()
        response = model.generate_content(prompt)
    except Exception as exc:  # в реална система би било по-добре по-прецизна обработка
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Грешка при извикване на AI модела: {exc}",
        )

    answer_text = getattr(response, "text", None)
    if not answer_text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI моделът не върна текстов отговор.",
        )

    return AIAnswer(answer=answer_text, data=data)