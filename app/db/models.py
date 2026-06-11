from app.db.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Text, Table
from sqlalchemy.orm import relationship


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True, unique=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, unique=True)

    staff = relationship("Staff", back_populates="user_account", uselist=False)
    student = relationship("Student", back_populates="user_account", uselist=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    degree = Column(String(50), nullable=True)
    field = Column(String(255), nullable=True)

    students = relationship("Student", back_populates="programme")
    courses = relationship("Course", back_populates="programme")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    faculty_number = Column(String(32), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    admission_year = Column(Integer, nullable=True)
    study_form = Column(String(50), nullable=True)

    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=True)
    programme = relationship("Programme", back_populates="students")

    user_account = relationship("User", back_populates="student", uselist=False)
    enrollments = relationship("Enrollment", back_populates="student")
    protocol_entries = relationship("ProtocolEntry", back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    semester = Column(Integer, nullable=True)
    mandatory_type = Column(String(20), nullable=True)
    credits = Column(Integer, nullable=True)
    hours_lectures = Column(Integer, nullable=True)
    hours_exercises = Column(Integer, nullable=True)

    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=True)
    programme = relationship("Programme", back_populates="courses")

    instances = relationship("CourseInstance", back_populates="course")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    position = Column(String(100), nullable=True)

    user_account = relationship("User", back_populates="staff", uselist=False)
    course_instances = relationship("CourseInstance", back_populates="teacher")
    exam_protocols = relationship("ExamProtocol", back_populates="teacher")


class CourseInstance(Base):
    __tablename__ = "course_instances"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), nullable=False)
    term = Column(String(10), nullable=True)
    group = Column(String(50), nullable=True)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    course = relationship("Course", back_populates="instances")

    teacher_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    teacher = relationship("Staff", back_populates="course_instances")

    enrollments = relationship("Enrollment", back_populates="course_instance")
    exam_sessions = relationship("ExamSession", back_populates="course_instance")
    exam_protocols = relationship("ExamProtocol", back_populates="course_instance")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_instance_id = Column(Integer, ForeignKey("course_instances.id"), nullable=False)
    status = Column(String(20), nullable=True)

    student = relationship("Student", back_populates="enrollments")
    course_instance = relationship("CourseInstance", back_populates="enrollments")

    grades = relationship("Grade", back_populates="enrollment")
    protocol_entries = relationship("ProtocolEntry", back_populates="enrollment")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    protocol_entry_id = Column(Integer, ForeignKey("protocol_entries.id"), nullable=True, unique=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    academic_year = Column(String(20), nullable=False)
    exam_date = Column(Date, nullable=True)

    grade_numeric = Column(Integer, nullable=True)
    grade_text_bg = Column(String(50), nullable=True)
    grade_ects = Column(String(5), nullable=True)
    is_transferred = Column(Boolean, default=False, nullable=False)

    enrollment = relationship("Enrollment", back_populates="grades")
    protocol_entry = relationship("ProtocolEntry", back_populates="grade")


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_instance_id = Column(Integer, ForeignKey("course_instances.id"), nullable=False)
    exam_type = Column(String(20), nullable=False)
    exam_date = Column(Date, nullable=False)
    academic_year = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    course_instance = relationship("CourseInstance", back_populates="exam_sessions")
    protocols = relationship("ExamProtocol", back_populates="exam_session", cascade="all, delete-orphan")


class ExamProtocol(Base):
    __tablename__ = "exam_protocols"

    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String(50), unique=True, index=True, nullable=False)
    protocol_type = Column(String(50), nullable=False)
    protocol_date = Column(Date, nullable=False)
    academic_year = Column(String(20), nullable=False)

    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id"), nullable=True)
    exam_session = relationship("ExamSession", back_populates="protocols")

    course_instance_id = Column(Integer, ForeignKey("course_instances.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    notes = Column(String(255), nullable=True)

    course_instance = relationship("CourseInstance", back_populates="exam_protocols")
    teacher = relationship("Staff", back_populates="exam_protocols")
    entries = relationship("ProtocolEntry", back_populates="protocol", cascade="all, delete-orphan")


class ProtocolEntry(Base):
    __tablename__ = "protocol_entries"

    id = Column(Integer, primary_key=True, index=True)

    protocol_id = Column(Integer, ForeignKey("exam_protocols.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=True)

    status = Column(String(50), nullable=True)
    notes = Column(String(255), nullable=True)

    protocol = relationship("ExamProtocol", back_populates="entries")
    student = relationship("Student", back_populates="protocol_entries")
    enrollment = relationship("Enrollment", back_populates="protocol_entries")
    grade = relationship("Grade", back_populates="protocol_entry", uselist=False)