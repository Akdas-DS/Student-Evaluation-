from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import csv
import io
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app import models, schemas, auth
from app.services.risk_service import ensure_enrollment, compute_and_store_risk, serialize_prediction

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def admin_required(current_user: models.User = Depends(auth.require_role("admin"))):
    return current_user


# ── Field Management ──
@router.get("/fields", response_model=List[schemas.FieldWithSemesters])
def list_fields(db: Session = Depends(get_db), _=Depends(admin_required)):
    fields = db.query(models.Field).all()
    result = []
    for f in fields:
        semesters = [schemas.SemesterOut.model_validate(s) for s in f.semesters]
        result.append(schemas.FieldWithSemesters(
            id=f.id, name=f.name, description=f.description,
            is_active=f.is_active, semesters=semesters
        ))
    return result


@router.post("/fields", response_model=schemas.FieldOut)
def create_field(data: schemas.FieldCreate, db: Session = Depends(get_db), _=Depends(admin_required)):
    if db.query(models.Field).filter(models.Field.name == data.name).first():
        raise HTTPException(status_code=400, detail="Field already exists")
    field = models.Field(name=data.name, description=data.description)
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/fields/{field_id}")
def delete_field(field_id: int, db: Session = Depends(get_db), _=Depends(admin_required)):
    field = db.query(models.Field).filter(models.Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    db.delete(field)
    db.commit()
    return {"detail": "Deleted"}


# ── Semester Management ──
@router.post("/semesters", response_model=schemas.SemesterOut)
def create_semester(data: schemas.SemesterCreate, db: Session = Depends(get_db), _=Depends(admin_required)):
    field = db.query(models.Field).filter(models.Field.id == data.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    existing = db.query(models.Semester).filter(
        models.Semester.field_id == data.field_id,
        models.Semester.number == data.number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Semester already exists for this field")
    sem = models.Semester(number=data.number, field_id=data.field_id)
    db.add(sem)
    db.commit()
    db.refresh(sem)
    return sem


@router.delete("/semesters/{sem_id}")
def delete_semester(sem_id: int, db: Session = Depends(get_db), _=Depends(admin_required)):
    sem = db.query(models.Semester).filter(models.Semester.id == sem_id).first()
    if not sem:
        raise HTTPException(status_code=404, detail="Semester not found")
    db.delete(sem)
    db.commit()
    return {"detail": "Deleted"}


# ── Subject Management ──
@router.get("/subjects", response_model=List[schemas.SubjectOut])
def list_all_subjects(db: Session = Depends(get_db), _=Depends(admin_required)):
    return db.query(models.Subject).all()


@router.get("/subjects/{semester_id}", response_model=List[schemas.SubjectWithQuestions])
def get_subjects_by_semester(semester_id: int, db: Session = Depends(get_db), _=Depends(admin_required)):
    subjects = db.query(models.Subject).filter(models.Subject.semester_id == semester_id).all()
    result = []
    for s in subjects:
        questions = [schemas.QuestionOut.model_validate(q) for q in s.questions]
        result.append(schemas.SubjectWithQuestions(
            id=s.id, name=s.name, code=s.code,
            semester_id=s.semester_id, questions=questions
        ))
    return result


@router.post("/subjects", response_model=schemas.SubjectOut)
def create_subject(data: schemas.SubjectCreate, db: Session = Depends(get_db), user=Depends(admin_required)):
    sem = db.query(models.Semester).filter(models.Semester.id == data.semester_id).first()
    if not sem:
        raise HTTPException(status_code=404, detail="Semester not found")
    subj = models.Subject(name=data.name, code=data.code, semester_id=data.semester_id, created_by=user.id)
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


@router.delete("/subjects/{subj_id}")
def delete_subject(subj_id: int, db: Session = Depends(get_db), _=Depends(admin_required)):
    subj = db.query(models.Subject).filter(models.Subject.id == subj_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subj)
    db.commit()
    return {"detail": "Deleted"}


# ── Question Management ──
@router.post("/questions", response_model=schemas.QuestionOut)
def create_question(data: schemas.QuestionCreate, db: Session = Depends(get_db), _=Depends(admin_required)):
    subj = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
    q = models.Question(**data.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/questions/{q_id}")
def delete_question(q_id: int, db: Session = Depends(get_db), _=Depends(admin_required)):
    q = db.query(models.Question).filter(models.Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"detail": "Deleted"}


# ── User Management ──
@router.get("/users")
def list_users(db: Session = Depends(get_db), _=Depends(admin_required)):
    users = db.query(models.User).all()
    return [schemas.UserOut.model_validate(u) for u in users]


@router.post("/users", response_model=schemas.UserOut)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), _=Depends(admin_required)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if data.student_id and db.query(models.User).filter(models.User.student_id == data.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already in use")

    user = models.User(
        name=data.name,
        email=data.email,
        password_hash=auth.hash_password(data.password),
        role=data.role,
        student_id=data.student_id if data.role == "student" else None,
        department=data.department if data.role == "student" else None,
        semester=data.semester if data.role == "student" else None,
        field_id=data.field_id if data.role == "student" else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "Deleted"}


# ── Teacher Assignment & Enrollments ──
@router.post("/teacher-subjects")
def assign_teacher_to_subject(data: schemas.TeacherSubjectAssign, db: Session = Depends(get_db), _=Depends(admin_required)):
    teacher = db.query(models.User).filter(models.User.id == data.teacher_id, models.User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    subject = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = db.query(models.TeacherSubject).filter(
        models.TeacherSubject.teacher_id == data.teacher_id,
        models.TeacherSubject.subject_id == data.subject_id,
    ).first()
    if existing:
        return {"detail": "Teacher already assigned to subject"}

    db.add(models.TeacherSubject(teacher_id=data.teacher_id, subject_id=data.subject_id))
    db.commit()
    return {"detail": "Teacher assigned to subject"}


@router.post("/enrollments", response_model=schemas.EnrollmentOut)
def create_enrollment(data: schemas.EnrollmentCreate, db: Session = Depends(get_db), _=Depends(admin_required)):
    student = db.query(models.User).filter(models.User.id == data.student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    subject = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    enrollment = ensure_enrollment(db, data.student_id, data.subject_id)
    enrollment.status = data.status
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/risk/subject/{subject_id}", response_model=List[schemas.RiskPredictionOut])
def get_subject_risk(subject_id: int, db: Session = Depends(get_db), _=Depends(admin_required)):
    enrollments = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.subject_id == subject_id, models.Enrollment.status == "active")
        .all()
    )
    return [serialize_prediction(db, e.student_id, e.subject_id) for e in enrollments]


@router.post("/final-results")
def record_final_result(data: schemas.FinalResultCreate, db: Session = Depends(get_db), admin=Depends(admin_required)):
    student = db.query(models.User).filter(models.User.id == data.student_id, models.User.role == "student").first()
    subject = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
    if not student or not subject:
        raise HTTPException(status_code=404, detail="Student or subject not found")

    ensure_enrollment(db, data.student_id, data.subject_id)
    result = (
        db.query(models.FinalResult)
        .filter(models.FinalResult.student_id == data.student_id, models.FinalResult.subject_id == data.subject_id)
        .first()
    )
    values = data.model_dump()
    if result:
        for key, value in values.items():
            setattr(result, key, value)
        result.recorded_by = admin.id
    else:
        result = models.FinalResult(**values, recorded_by=admin.id)
        db.add(result)

    compute_and_store_risk(db, data.student_id, data.subject_id)
    db.commit()
    return {"detail": "Final result recorded"}


# ── Analytics ──
@router.get("/analytics", response_model=schemas.AnalyticsOut)
def get_analytics(db: Session = Depends(get_db), _=Depends(admin_required)):
    total_students = db.query(models.User).filter(models.User.role == "student").count()
    total_assessments = db.query(models.Assessment).count()

    low = db.query(models.Assessment).filter(models.Assessment.risk_level == "Low").count()
    medium = db.query(models.Assessment).filter(models.Assessment.risk_level == "Medium").count()
    high = db.query(models.Assessment).filter(models.Assessment.risk_level == "High").count()

    subject_stats = (
        db.query(
            models.Subject.name,
            func.avg(models.Assessment.risk_score).label("avg_risk"),
            func.count(models.Assessment.id).label("total"),
        )
        .join(models.Assessment, models.Assessment.subject_id == models.Subject.id)
        .group_by(models.Subject.name)
        .all()
    )
    subject_risks = [
        schemas.SubjectRisk(subject_name=s[0], avg_risk=round(s[1], 1), total_assessments=s[2])
        for s in subject_stats
    ]

    high_risk_list = (
        db.query(models.Assessment)
        .filter(models.Assessment.risk_level == "High")
        .order_by(models.Assessment.risk_score.desc())
        .limit(20)
        .all()
    )
    high_risk_students = [
        schemas.HighRiskStudent(
            student_name=a.student.name,
            student_email=a.student.email,
            subject_name=a.subject.name,
            risk_score=round(a.risk_score, 1),
            risk_level=a.risk_level,
        )
        for a in high_risk_list
    ]

    return schemas.AnalyticsOut(
        total_students=total_students,
        total_assessments=total_assessments,
        risk_distribution=schemas.RiskDistribution(low=low, medium=medium, high=high),
        subject_risks=subject_risks,
        high_risk_students=high_risk_students,
    )


# ── Bulk Student Enrollment ──
@router.post("/enrollments/bulk")
async def bulk_enroll_students(
    subject_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(admin_required),
):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded CSV")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty CSV file")

    required = ["name", "email", "student_id"]
    for req in required:
        if req not in reader.fieldnames:
            raise HTTPException(status_code=400, detail=f"Missing required CSV column: {req}. Found: {', '.join(reader.fieldnames)}")

    success_count = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        email = row.get("email", "").strip()
        st_id = row.get("student_id", "").strip()

        if not email or not name or not st_id:
            errors.append(f"Row {row_num}: Missing name, email, or student_id")
            continue

        student = db.query(models.User).filter(models.User.email == email).first()
        if not student:
            if db.query(models.User).filter(models.User.student_id == st_id).first():
                errors.append(f"Row {row_num}: Student ID {st_id} is already in use")
                continue
                
            student = models.User(
                name=name,
                email=email,
                student_id=st_id,
                password_hash=auth.hash_password("student123"),
                role="student"
            )
            db.add(student)
            db.commit()
            db.refresh(student)
        
        existing = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student.id,
            models.Enrollment.subject_id == subject_id
        ).first()

        if not existing:
            db.add(models.Enrollment(student_id=student.id, subject_id=subject_id))
            success_count += 1
            
    db.commit()
    return {
        "success_count": success_count,
        "errors": errors,
        "message": f"Successfully enrolled/created {success_count} students. {len(errors)} errors found."
    }

from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/export/risk-report")
def export_risk_report(db: Session = Depends(get_db), _=Depends(admin_required)):
    # Simple risk report export
    assessments = db.query(models.RiskPrediction).all()
    # To keep it simple, just grab the latest prediction for each student/subject
    
    # Let's just output raw enrollments and their latest risk
    enrollments = db.query(models.Enrollment).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Student Email", "Student ID", "Subject", "Risk Score", "Risk Level", "Archetype", "Confidence"])
    
    for e in enrollments:
        student = db.query(models.User).filter(models.User.id == e.student_id).first()
        subject = db.query(models.Subject).filter(models.Subject.id == e.subject_id).first()
        
        # Get latest risk
        risk = db.query(models.RiskPrediction).filter(
            models.RiskPrediction.student_id == e.student_id,
            models.RiskPrediction.subject_id == e.subject_id
        ).order_by(models.RiskPrediction.created_at.desc()).first()
        
        if risk:
            import json
            factors = json.loads(risk.factors_json) if risk.factors_json else {}
            archetype = factors.get("archetype", "Unknown")
            
            writer.writerow([
                student.name,
                student.email,
                student.student_id or "-",
                subject.name,
                round(risk.risk_score, 1),
                risk.risk_level,
                archetype,
                risk.confidence
            ])
        else:
            writer.writerow([
                student.name,
                student.email,
                student.student_id or "-",
                subject.name,
                "N/A", "N/A", "N/A", "N/A"
            ])
            
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=risk_report.csv"
    return response
