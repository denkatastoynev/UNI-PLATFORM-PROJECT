from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    faculty_number: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    admission_year: Optional[int] = None
    study_form: Optional[str] = None
    programme_id: Optional[int] = None


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CourseBase(BaseModel):
    code: str
    name: str
    semester: Optional[int] = None
    mandatory_type: Optional[str] = None
    credits: Optional[int] = None
    hours_lectures: Optional[int] = None
    hours_exercises: Optional[int] = None
    programme_id: Optional[int] = None


class CourseCreate(CourseBase):
    pass


class CourseRead(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class GradeBase(BaseModel):
    enrollment_id: int
    academic_year: str
    exam_date: Optional[date] = None
    grade_numeric: Optional[int] = None
    grade_text_bg: Optional[str] = None
    grade_ects: Optional[str] = None
    is_transferred: Optional[bool] = False
    protocol_entry_id: Optional[int] = None


class GradeCreate(GradeBase):
    pass


class GradeRead(GradeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)