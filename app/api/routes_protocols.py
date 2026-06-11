from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db import models
from app.api.common_schemas import MessageResponse
from app.core.security import require_roles

router = APIRouter()


def _get_protocol_or_404(db: Session, protocol_id: int):
    protocol = (
        db.query(models.ExamProtocol)
        .options(
            joinedload(models.ExamProtocol.course_instance).joinedload(models.CourseInstance.course),
            joinedload(models.ExamProtocol.teacher),
            joinedload(models.ExamProtocol.entries).joinedload(models.ProtocolEntry.student),
            joinedload(models.ExamProtocol.entries).joinedload(models.ProtocolEntry.enrollment),
            joinedload(models.ExamProtocol.entries).joinedload(models.ProtocolEntry.grade),
        )
        .filter(models.ExamProtocol.id == protocol_id)
        .first()
    )
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@router.get("/")
def list_protocols(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    academic_year: Optional[str] = None,
    protocol_type: Optional[str] = None,
    course_instance_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    query = (
        db.query(models.ExamProtocol)
        .options(
            joinedload(models.ExamProtocol.course_instance).joinedload(models.CourseInstance.course),
            joinedload(models.ExamProtocol.teacher),
        )
        .order_by(models.ExamProtocol.protocol_date.desc(), models.ExamProtocol.id.desc())
    )

    if academic_year:
        query = query.filter(models.ExamProtocol.academic_year == academic_year)
    if protocol_type:
        query = query.filter(models.ExamProtocol.protocol_type == protocol_type)
    if course_instance_id:
        query = query.filter(models.ExamProtocol.course_instance_id == course_instance_id)
    if teacher_id:
        query = query.filter(models.ExamProtocol.teacher_id == teacher_id)

    protocols = query.offset(skip).limit(limit).all()

    return [
        {
            "id": p.id,
            "protocol_number": p.protocol_number,
            "protocol_type": p.protocol_type,
            "protocol_date": p.protocol_date,
            "academic_year": p.academic_year,
            "course_instance_id": p.course_instance_id,
            "course_name": p.course_instance.course.name if p.course_instance and p.course_instance.course else None,
            "teacher_id": p.teacher_id,
            "teacher_name": p.teacher.name if p.teacher else None,
            "notes": p.notes,
        }
        for p in protocols
    ]


@router.get("/{protocol_id}")
def get_protocol(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    protocol = _get_protocol_or_404(db, protocol_id)

    return {
        "id": protocol.id,
        "protocol_number": protocol.protocol_number,
        "protocol_type": protocol.protocol_type,
        "protocol_date": protocol.protocol_date,
        "academic_year": protocol.academic_year,
        "course_instance_id": protocol.course_instance_id,
        "course_name": protocol.course_instance.course.name
        if protocol.course_instance and protocol.course_instance.course
        else None,
        "teacher_id": protocol.teacher_id,
        "teacher_name": protocol.teacher.name if protocol.teacher else None,
        "notes": protocol.notes,
        "entries": [
            {
                "id": entry.id,
                "student_id": entry.student_id,
                "faculty_number": entry.student.faculty_number if entry.student else None,
                "student_name": (
                    f"{entry.student.first_name} {entry.student.last_name}"
                    if entry.student else None
                ),
                "enrollment_id": entry.enrollment_id,
                "grade_id": entry.grade_id,
                "grade_numeric": entry.grade.grade_numeric if entry.grade else None,
                "grade_text_bg": entry.grade.grade_text_bg if entry.grade else None,
                "grade_ects": entry.grade.grade_ects if entry.grade else None,
                "status": entry.status,
                "notes": entry.notes,
            }
            for entry in protocol.entries
        ],
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_protocol(
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    required_fields = [
        "protocol_number",
        "protocol_type",
        "protocol_date",
        "academic_year",
        "course_instance_id",
    ]
    for field in required_fields:
        if field not in payload or payload[field] in (None, ""):
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    existing = (
        db.query(models.ExamProtocol)
        .filter(models.ExamProtocol.protocol_number == payload["protocol_number"])
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Protocol number already exists")

    course_instance = (
        db.query(models.CourseInstance)
        .filter(models.CourseInstance.id == payload["course_instance_id"])
        .first()
    )
    if not course_instance:
        raise HTTPException(status_code=404, detail="Course instance not found")

    teacher_id = payload.get("teacher_id")
    if teacher_id is not None:
        teacher = db.query(models.Staff).filter(models.Staff.id == teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

    protocol = models.ExamProtocol(
        protocol_number=payload["protocol_number"],
        protocol_type=payload["protocol_type"],
        protocol_date=payload["protocol_date"],
        academic_year=payload["academic_year"],
        course_instance_id=payload["course_instance_id"],
        teacher_id=payload.get("teacher_id"),
        notes=payload.get("notes"),
    )

    db.add(protocol)
    db.commit()
    db.refresh(protocol)

    return {
        "message": "Protocol created successfully",
        "id": protocol.id,
    }


@router.put("/{protocol_id}")
def update_protocol(
    protocol_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    protocol = db.query(models.ExamProtocol).filter(models.ExamProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    if "protocol_number" in payload and payload["protocol_number"] != protocol.protocol_number:
        existing = (
            db.query(models.ExamProtocol)
            .filter(
                models.ExamProtocol.protocol_number == payload["protocol_number"],
                models.ExamProtocol.id != protocol_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Protocol number already exists")
        protocol.protocol_number = payload["protocol_number"]

    if "protocol_type" in payload:
        protocol.protocol_type = payload["protocol_type"]

    if "protocol_date" in payload:
        protocol.protocol_date = payload["protocol_date"]

    if "academic_year" in payload:
        protocol.academic_year = payload["academic_year"]

    if "course_instance_id" in payload:
        course_instance = (
            db.query(models.CourseInstance)
            .filter(models.CourseInstance.id == payload["course_instance_id"])
            .first()
        )
        if not course_instance:
            raise HTTPException(status_code=404, detail="Course instance not found")
        protocol.course_instance_id = payload["course_instance_id"]

    if "teacher_id" in payload:
        teacher_id = payload["teacher_id"]
        if teacher_id is not None:
            teacher = db.query(models.Staff).filter(models.Staff.id == teacher_id).first()
            if not teacher:
                raise HTTPException(status_code=404, detail="Teacher not found")
        protocol.teacher_id = teacher_id

    if "notes" in payload:
        protocol.notes = payload["notes"]

    db.commit()
    db.refresh(protocol)

    return {
        "message": "Protocol updated successfully",
        "id": protocol.id,
    }


@router.delete("/{protocol_id}")
def delete_protocol(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    protocol = db.query(models.ExamProtocol).filter(models.ExamProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    db.delete(protocol)
    db.commit()

    return {"message": "Protocol deleted successfully"}


@router.get("/{protocol_id}/entries")
def list_protocol_entries(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    protocol = _get_protocol_or_404(db, protocol_id)

    return [
        {
            "id": entry.id,
            "student_id": entry.student_id,
            "faculty_number": entry.student.faculty_number if entry.student else None,
            "student_name": (
                f"{entry.student.first_name} {entry.student.last_name}"
                if entry.student else None
            ),
            "enrollment_id": entry.enrollment_id,
            "grade_id": entry.grade_id,
            "grade_numeric": entry.grade.grade_numeric if entry.grade else None,
            "grade_text_bg": entry.grade.grade_text_bg if entry.grade else None,
            "grade_ects": entry.grade.grade_ects if entry.grade else None,
            "status": entry.status,
            "notes": entry.notes,
        }
        for entry in protocol.entries
    ]


@router.post("/{protocol_id}/entries", status_code=status.HTTP_201_CREATED)
def add_protocol_entry(
    protocol_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    protocol = db.query(models.ExamProtocol).filter(models.ExamProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    required_fields = ["student_id"]
    for field in required_fields:
        if field not in payload or payload[field] in (None, ""):
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    student = db.query(models.Student).filter(models.Student.id == payload["student_id"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollment_id = payload.get("enrollment_id")
    enrollment = None
    if enrollment_id is not None:
        enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")

    grade_id = payload.get("grade_id")
    grade = None
    if grade_id is not None:
        grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
        if not grade:
            raise HTTPException(status_code=404, detail="Grade not found")

    existing = (
        db.query(models.ProtocolEntry)
        .filter(
            models.ProtocolEntry.protocol_id == protocol_id,
            models.ProtocolEntry.student_id == payload["student_id"],
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists in this protocol")

    entry = models.ProtocolEntry(
        protocol_id=protocol_id,
        student_id=payload["student_id"],
        enrollment_id=enrollment_id,
        grade_id=grade_id,
        status=payload.get("status"),
        notes=payload.get("notes"),
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "message": "Protocol entry added successfully",
        "id": entry.id,
    }


@router.put("/entries/{entry_id}")
def update_protocol_entry(
    entry_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    entry = db.query(models.ProtocolEntry).filter(models.ProtocolEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Protocol entry not found")

    if "student_id" in payload:
        student = db.query(models.Student).filter(models.Student.id == payload["student_id"]).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        duplicate = (
            db.query(models.ProtocolEntry)
            .filter(
                models.ProtocolEntry.protocol_id == entry.protocol_id,
                models.ProtocolEntry.student_id == payload["student_id"],
                models.ProtocolEntry.id != entry_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=400, detail="Student already exists in this protocol")
        entry.student_id = payload["student_id"]

    if "enrollment_id" in payload:
        enrollment_id = payload["enrollment_id"]
        if enrollment_id is not None:
            enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
            if not enrollment:
                raise HTTPException(status_code=404, detail="Enrollment not found")
        entry.enrollment_id = enrollment_id

    if "grade_id" in payload:
        grade_id = payload["grade_id"]
        if grade_id is not None:
            grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
            if not grade:
                raise HTTPException(status_code=404, detail="Grade not found")
        entry.grade_id = grade_id

    if "status" in payload:
        entry.status = payload["status"]

    if "notes" in payload:
        entry.notes = payload["notes"]

    db.commit()
    db.refresh(entry)

    return {
        "message": "Protocol entry updated successfully",
        "id": entry.id,
    }


@router.delete("/entries/{entry_id}")
def delete_protocol_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    entry = db.query(models.ProtocolEntry).filter(models.ProtocolEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Protocol entry not found")

    db.delete(entry)
    db.commit()

    return {"message": "Protocol entry deleted successfully"}


@router.post(
    "/{protocol_id}/generate-from-enrollments",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_protocol_from_enrollments(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "secretary", "teacher")),
):
    protocol = db.query(models.ExamProtocol).filter(models.ExamProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    enrollments = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.course_instance_id == protocol.course_instance_id)
        .all()
    )

    created = 0

    for enrollment in enrollments:
        existing = (
            db.query(models.ProtocolEntry)
            .filter(
                models.ProtocolEntry.protocol_id == protocol_id,
                models.ProtocolEntry.student_id == enrollment.student_id,
            )
            .first()
        )
        if existing:
            continue

        entry = models.ProtocolEntry(
            protocol_id=protocol_id,
            student_id=enrollment.student_id,
            enrollment_id=enrollment.id,
            grade_id=None,
            status=enrollment.status,
            notes=None,
        )
        db.add(entry)
        created += 1

    db.commit()

    return MessageResponse(
        message=f"Protocol generated from enrollments. Created entries: {created}"
    )