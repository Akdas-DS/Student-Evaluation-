from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ── Auth Schemas ──
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6)
    role: str = Field(default="student", pattern="^(admin|teacher|student)$")
    student_id: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    field_id: Optional[int] = None


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(admin|teacher|student)$")
    student_id: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    field_id: Optional[int] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    student_id: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    field_id: Optional[int] = None

    class Config:
        from_attributes = True


# ── Field Schemas ──
class FieldCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class FieldOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class FieldWithSemesters(FieldOut):
    semesters: List["SemesterOut"] = []


# ── Semester Schemas ──
class SemesterCreate(BaseModel):
    number: int = Field(..., ge=1, le=12)
    field_id: int


class SemesterOut(BaseModel):
    id: int
    number: int
    field_id: int

    class Config:
        from_attributes = True


class SemesterWithSubjects(SemesterOut):
    subjects: List["SubjectOut"] = []


# ── Subject Schemas ──
class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    code: Optional[str] = None
    semester_id: int


class SubjectOut(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    semester_id: int

    class Config:
        from_attributes = True


class SubjectWithQuestions(SubjectOut):
    questions: List["QuestionOut"] = []


# ── Question Schemas ──
class QuestionCreate(BaseModel):
    subject_id: int
    text: str = Field(..., min_length=5)
    category: str = Field(..., min_length=2, max_length=100)
    weight: float = Field(default=1.0, ge=0.1, le=10.0)
    min_val: int = Field(default=0, ge=0)
    max_val: int = Field(default=10, ge=1)
    order_index: int = Field(default=0, ge=0)


class QuestionOut(BaseModel):
    id: int
    subject_id: int
    text: str
    category: str
    weight: float
    min_val: int
    max_val: int
    order_index: int

    class Config:
        from_attributes = True


# ── Assessment Schemas ──
class AnswerSubmit(BaseModel):
    question_id: int
    answer_value: float


class AssessmentSubmit(BaseModel):
    subject_id: int
    answers: List[AnswerSubmit]


class AssessmentOut(BaseModel):
    id: int
    subject_id: int
    risk_score: float
    risk_level: str
    factors: Optional[dict] = None
    recommendations: Optional[dict] = None
    subject_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Academic Data Schemas ──
class TeacherSubjectAssign(BaseModel):
    teacher_id: int
    subject_id: int


class EnrollmentCreate(BaseModel):
    student_id: int
    subject_id: int
    status: str = Field(default="active", pattern="^(active|inactive|completed)$")


class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceRecordCreate(BaseModel):
    student_id: int
    subject_id: int
    attended_classes: int = Field(..., ge=0)
    total_classes: int = Field(..., ge=1)
    notes: Optional[str] = None


class AssignmentRecordCreate(BaseModel):
    student_id: int
    subject_id: int
    title: str = Field(..., min_length=2, max_length=150)
    submitted: bool = True
    score: Optional[float] = Field(default=None, ge=0)
    max_score: float = Field(default=100.0, gt=0)
    notes: Optional[str] = None


class InternalExamScoreCreate(BaseModel):
    student_id: int
    subject_id: int
    exam_name: str = Field(..., min_length=2, max_length=100)
    score: float = Field(..., ge=0)
    max_score: float = Field(default=100.0, gt=0)
    notes: Optional[str] = None


class PracticalScoreCreate(BaseModel):
    student_id: int
    subject_id: int
    title: str = Field(..., min_length=2, max_length=100)
    score: float = Field(..., ge=0)
    max_score: float = Field(default=100.0, gt=0)
    notes: Optional[str] = None


class FinalResultCreate(BaseModel):
    student_id: int
    subject_id: int
    final_marks: Optional[float] = Field(default=None, ge=0)
    max_marks: float = Field(default=100.0, gt=0)
    got_kt: bool
    result_label: Optional[str] = None


class InterventionCreate(BaseModel):
    student_id: int
    subject_id: int
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    due_at: Optional[datetime] = None


class InterventionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(open|in_progress|completed|cancelled)$")
    due_at: Optional[datetime] = None


class InterventionOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    teacher_id: int
    title: str
    description: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskPredictionOut(BaseModel):
    student_id: int
    subject_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    subject_name: Optional[str] = None
    risk_score: float
    risk_level: str
    confidence: str
    data_completeness: float
    factors: dict
    recommendations: dict
    created_at: Optional[datetime] = None


class PerformanceRecordOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    recorded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Analytics Schemas ──
class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int


class SubjectRisk(BaseModel):
    subject_name: str
    avg_risk: float
    total_assessments: int


class HighRiskStudent(BaseModel):
    student_name: str
    student_email: str
    subject_name: str
    risk_score: float
    risk_level: str


class AnalyticsOut(BaseModel):
    total_students: int
    total_assessments: int
    risk_distribution: RiskDistribution
    subject_risks: List[SubjectRisk]
    high_risk_students: List[HighRiskStudent]


# Resolve forward refs
TokenResponse.model_rebuild()
FieldWithSemesters.model_rebuild()
SemesterWithSubjects.model_rebuild()
SubjectWithQuestions.model_rebuild()


class PasswordResetRequest(BaseModel):
    email: str
    new_password: str = Field(..., min_length=8)
