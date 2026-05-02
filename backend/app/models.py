from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, teacher, student
    student_id = Column(String(50), unique=True, nullable=True)
    department = Column(String(100), nullable=True)
    semester = Column(Integer, nullable=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    field = relationship("Field", back_populates="users")
    assessments = relationship("Assessment", back_populates="student")
    created_subjects = relationship("Subject", back_populates="creator")


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="field")
    semesters = relationship("Semester", back_populates="field", cascade="all, delete-orphan")


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)

    field = relationship("Field", back_populates="semesters")
    subjects = relationship("Subject", back_populates="semester", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(20), nullable=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    semester = relationship("Semester", back_populates="subjects")
    creator = relationship("User", back_populates="created_subjects")
    questions = relationship("Question", back_populates="subject", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="subject")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # e.g., 'programming', 'theory', 'math'
    weight = Column(Float, default=1.0)
    min_val = Column(Integer, default=0)
    max_val = Column(Integer, default=10)
    order_index = Column(Integer, default=0)

    subject = relationship("Subject", back_populates="questions")
    answers = relationship("AssessmentAnswer", back_populates="question")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High
    factors_json = Column(Text, nullable=True)
    recommendation_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("User", back_populates="assessments")
    subject = relationship("Subject", back_populates="assessments")
    answers = relationship("AssessmentAnswer", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_value = Column(Float, nullable=False)

    assessment = relationship("Assessment", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"
    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject"),)

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "subject_id", name="uq_student_subject_enrollment"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    attended_classes = Column(Integer, nullable=False)
    total_classes = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AssignmentRecord(Base):
    __tablename__ = "assignment_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(150), nullable=False)
    submitted = Column(Boolean, default=True)
    score = Column(Float, nullable=True)
    max_score = Column(Float, default=100.0)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class InternalExamScore(Base):
    __tablename__ = "internal_exam_scores"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    exam_name = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PracticalScore(Base):
    __tablename__ = "practical_scores"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FinalResult(Base):
    __tablename__ = "final_results"
    __table_args__ = (UniqueConstraint("student_id", "subject_id", name="uq_student_subject_final_result"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    final_marks = Column(Float, nullable=True)
    max_marks = Column(Float, default=100.0)
    got_kt = Column(Boolean, nullable=False)
    result_label = Column(String(30), nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="open")  # open, in_progress, completed, cancelled
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence = Column(String(20), nullable=False)
    data_completeness = Column(Float, nullable=False)
    factors_json = Column(Text, nullable=True)
    recommendations_json = Column(Text, nullable=True)
    model_version = Column(String(50), default="rules-v1")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who made the change
    action = Column(String(50), nullable=False)  # e.g., 'CREATE', 'UPDATE', 'DELETE'
    entity_type = Column(String(50), nullable=False)  # e.g., 'AttendanceRecord', 'InternalScore'
    entity_id = Column(Integer, nullable=False)
    old_value = Column(Text, nullable=True)  # JSON representation of old state
    new_value = Column(Text, nullable=True)  # JSON representation of new state
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

