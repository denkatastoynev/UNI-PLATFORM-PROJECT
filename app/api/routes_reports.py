from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db import models
from app.core.security import require_roles

router = APIRouter()


class MessageResponse(BaseModel):
    message: str


class StudentGradeItem(BaseModel):
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    academic_year: Optional[str] = None
    exam_date: Optional[str] = None
    grade_numeric: Optional[int] = None
    grade_text_bg: Optional[str] = None
    grade_ects: Optional[str] = None


class StudentGradesReport(BaseModel):
    faculty_number: str
    student_name: str
    programme_code: Optional[str] = None
    grades: List[StudentGradeItem]


class CourseInstanceStudentItem(BaseModel):
    faculty_number: Optional[str] = None
    student_name: Optional[str] = None
    status: Optional[str] = None
    grade_numeric: Optional[int] = None
    grade_text_bg: Optional[str] = None
    grade_ects: Optional[str] = None


class CourseInstanceReport(BaseModel):
    course_instance_id: int
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    academic_year: Optional[str] = None
    term: Optional[str] = None
    students: List[CourseInstanceStudentItem]


class StudentAverageReport(BaseModel):
    faculty_number: str
    student_name: str
    grades_count: int
    average_grade: Optional[float] = None


class CourseAverageReport(BaseModel):
    course_instance_id: int
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    academic_year: Optional[str] = None
    term: Optional[str] = None
    grades_count: int
    average_grade: Optional[float] = None


class ExcellentStudentItem(BaseModel):
    faculty_number: str
    student_name: str
    programme_code: Optional[str] = None
    grades_count: int
    average_grade: float


@router.get("/student-grades/{faculty_number}", response_model=StudentGradesReport)
def get_student_grades_report(
    faculty_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    student = db.query(models.Student).filter_by(faculty_number=faculty_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студентът не е намерен.")

    result_grades = []

    for enrollment in student.enrollments:
        ci = enrollment.course_instance
        course = ci.course if ci else None

        for grade in enrollment.grades:
            result_grades.append(
                StudentGradeItem(
                    course_code=course.code if course else None,
                    course_name=course.name if course else None,
                    academic_year=grade.academic_year,
                    exam_date=str(grade.exam_date) if grade.exam_date else None,
                    grade_numeric=grade.grade_numeric,
                    grade_text_bg=grade.grade_text_bg,
                    grade_ects=grade.grade_ects,
                )
            )

    return StudentGradesReport(
        faculty_number=student.faculty_number,
        student_name=f"{student.first_name} {student.last_name}",
        programme_code=student.programme.code if student.programme else None,
        grades=result_grades,
    )


@router.get("/course-instance/{course_instance_id}", response_model=CourseInstanceReport)
def get_course_instance_report(
    course_instance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    ci = db.query(models.CourseInstance).filter_by(id=course_instance_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Провеждането не е намерено.")

    items = []

    for enrollment in ci.enrollments:
        latest_grade = enrollment.grades[-1] if enrollment.grades else None

        items.append(
            CourseInstanceStudentItem(
                faculty_number=enrollment.student.faculty_number if enrollment.student else None,
                student_name=(
                    f"{enrollment.student.first_name} {enrollment.student.last_name}"
                    if enrollment.student else None
                ),
                status=enrollment.status,
                grade_numeric=latest_grade.grade_numeric if latest_grade else None,
                grade_text_bg=latest_grade.grade_text_bg if latest_grade else None,
                grade_ects=latest_grade.grade_ects if latest_grade else None,
            )
        )

    return CourseInstanceReport(
        course_instance_id=ci.id,
        course_code=ci.course.code if ci.course else None,
        course_name=ci.course.name if ci.course else None,
        academic_year=ci.academic_year,
        term=ci.term,
        students=items,
    )


@router.get("/student-average/{faculty_number}", response_model=StudentAverageReport)
def get_student_average_report(
    faculty_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    student = db.query(models.Student).filter_by(faculty_number=faculty_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студентът не е намерен.")

    numeric_grades = []

    for enrollment in student.enrollments:
        for grade in enrollment.grades:
            if grade.grade_numeric is not None:
                numeric_grades.append(grade.grade_numeric)

    avg = None
    if numeric_grades:
        avg = round(sum(numeric_grades) / len(numeric_grades), 2)

    return StudentAverageReport(
        faculty_number=student.faculty_number,
        student_name=f"{student.first_name} {student.last_name}",
        grades_count=len(numeric_grades),
        average_grade=avg,
    )


@router.get("/course-average/{course_instance_id}", response_model=CourseAverageReport)
def get_course_average_report(
    course_instance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    ci = db.query(models.CourseInstance).filter_by(id=course_instance_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Провеждането не е намерено.")

    numeric_grades = []

    for enrollment in ci.enrollments:
        for grade in enrollment.grades:
            if grade.grade_numeric is not None:
                numeric_grades.append(grade.grade_numeric)

    avg = None
    if numeric_grades:
        avg = round(sum(numeric_grades) / len(numeric_grades), 2)

    return CourseAverageReport(
        course_instance_id=ci.id,
        course_code=ci.course.code if ci.course else None,
        course_name=ci.course.name if ci.course else None,
        academic_year=ci.academic_year,
        term=ci.term,
        grades_count=len(numeric_grades),
        average_grade=avg,
    )


@router.get("/excellent-students", response_model=List[ExcellentStudentItem])
def get_excellent_students_report(
    academic_year: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    students = db.query(models.Student).all()
    result = []

    for student in students:
        numeric_grades = []

        for enrollment in student.enrollments:
            for grade in enrollment.grades:
                if grade.academic_year == academic_year and grade.grade_numeric is not None:
                    numeric_grades.append(grade.grade_numeric)

        if numeric_grades:
            avg = round(sum(numeric_grades) / len(numeric_grades), 2)
            if avg >= 5.50:
                result.append(
                    ExcellentStudentItem(
                        faculty_number=student.faculty_number,
                        student_name=f"{student.first_name} {student.last_name}",
                        programme_code=student.programme.code if student.programme else None,
                        grades_count=len(numeric_grades),
                        average_grade=avg,
                    )
                )

    result.sort(key=lambda x: x.average_grade, reverse=True)
    return result


@router.get("/student-profile/{student_id}", summary="Студентски профил / академична справка")
def get_student_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    student = (
        db.query(models.Student)
        .options(joinedload(models.Student.programme))
        .filter(models.Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Няма намерен студент с посочения идентификатор.",
        )

    enrollments = (
        db.query(models.Enrollment)
        .options(
            joinedload(models.Enrollment.course_instance).joinedload(models.CourseInstance.course),
            joinedload(models.Enrollment.course_instance).joinedload(models.CourseInstance.teacher),
            joinedload(models.Enrollment.grades).joinedload(models.Grade.protocol_entry).joinedload(models.ProtocolEntry.protocol),
        )
        .filter(models.Enrollment.student_id == student_id)
        .all()
    )

    academic_records: List[Dict[str, Any]] = []

    for enrollment in enrollments:
        course_instance = enrollment.course_instance
        course = course_instance.course if course_instance else None
        teacher = course_instance.teacher if course_instance else None

        grades_sorted = sorted(
            [g for g in enrollment.grades if g.grade_numeric is not None],
            key=lambda g: g.grade_numeric,
            reverse=True,
        )

        best_grade = grades_sorted[0] if grades_sorted else None

        all_grades = []
        for grade in enrollment.grades:
            protocol = None
            protocol_type = None
            protocol_number = None
            protocol_date = None

            if grade.protocol_entry and grade.protocol_entry.protocol:
                protocol = grade.protocol_entry.protocol
                protocol_type = protocol.protocol_type
                protocol_number = protocol.protocol_number
                protocol_date = protocol.protocol_date

            all_grades.append(
                {
                    "grade_id": grade.id,
                    "protocol_entry_id": grade.protocol_entry_id,
                    "academic_year": grade.academic_year,
                    "exam_date": grade.exam_date.isoformat() if grade.exam_date else None,
                    "grade_numeric": grade.grade_numeric,
                    "grade_text_bg": grade.grade_text_bg,
                    "grade_ects": grade.grade_ects,
                    "is_transferred": grade.is_transferred,
                    "protocol_type": protocol_type,
                    "protocol_number": protocol_number,
                    "protocol_date": protocol_date.isoformat() if protocol_date else None,
                }
            )

        academic_records.append(
            {
                "enrollment_id": enrollment.id,
                "status": enrollment.status,
                "course_instance": {
                    "id": course_instance.id if course_instance else None,
                    "academic_year": course_instance.academic_year if course_instance else None,
                    "term": course_instance.term if course_instance else None,
                    "group": course_instance.group if course_instance else None,
                },
                "course": {
                    "id": course.id if course else None,
                    "code": course.code if course else None,
                    "name": course.name if course else None,
                    "semester": course.semester if course else None,
                    "credits": course.credits if course else None,
                    "mandatory_type": course.mandatory_type if course else None,
                },
                "teacher": {
                    "id": teacher.id if teacher else None,
                    "name": teacher.name if teacher else None,
                    "position": teacher.position if teacher else None,
                },
                "best_grade": {
                    "grade_id": best_grade.id if best_grade else None,
                    "grade_numeric": best_grade.grade_numeric if best_grade else None,
                    "grade_text_bg": best_grade.grade_text_bg if best_grade else None,
                    "grade_ects": best_grade.grade_ects if best_grade else None,
                    "exam_date": best_grade.exam_date.isoformat() if best_grade and best_grade.exam_date else None,
                    "protocol_type": (
                        best_grade.protocol_entry.protocol.protocol_type
                        if best_grade and best_grade.protocol_entry and best_grade.protocol_entry.protocol
                        else None
                    ),
                    "protocol_number": (
                        best_grade.protocol_entry.protocol.protocol_number
                        if best_grade and best_grade.protocol_entry and best_grade.protocol_entry.protocol
                        else None
                    ),
                },
                "all_grades": all_grades,
            }
        )

    return {
        "student": {
            "id": student.id,
            "faculty_number": student.faculty_number,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "admission_year": student.admission_year,
            "study_form": student.study_form,
            "programme": {
                "id": student.programme.id if student.programme else None,
                "code": student.programme.code if student.programme else None,
                "name": student.programme.name if student.programme else None,
                "degree": student.programme.degree if student.programme else None,
            },
        },
        "academic_records": academic_records,
    }