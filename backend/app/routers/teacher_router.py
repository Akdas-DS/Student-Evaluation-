from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import csv
import io
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app import models, schemas, auth
from app.services.risk_service import ensure_enrollment, compute_and_store_risk, serialize_prediction

router = APIRouter(prefix="/api/teacher", tags=["Teacher"])


def teacher_required(current_user: models.User = Depends(auth.require_role("teacher", "admin"))):
    return current_user


def _teacher_subject_ids(db: Session, user: models.User) -> List[int]:
    if user.role == "admin":
        return [row[0] for row in db.query(models.Subject.id).all()]
    created_ids = [row[0] for row in db.query(models.Subject.id).filter(models.Subject.created_by == user.id).all()]
    assigned_ids = [
        row[0]
        for row in db.query(models.TeacherSubject.subject_id).filter(models.TeacherSubject.teacher_id == user.id).all()
    ]
    return sorted(set(created_ids + assigned_ids))


def _ensure_subject_access(db: Session, user: models.User, subject_id: int):
    if subject_id not in _teacher_subject_ids(db, user):
        raise HTTPException(status_code=403, detail="You are not assigned to this subject")


def _ensure_student(db: Session, student_id: int):
    student = db.query(models.User).filter(models.User.id == student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _record_response(db: Session, record, student_id: int, subject_id: int):
    db.flush()
    compute_and_store_risk(db, student_id, subject_id)
    db.commit()
    db.refresh(record)
    return {"record_id": record.id, "risk": serialize_prediction(db, student_id, subject_id)}


# ── Subject Management (Teacher can create subjects in any semester) ──
@router.get("/fields", response_model=List[schemas.FieldWithSemesters])
def list_fields(db: Session = Depends(get_db), _=Depends(teacher_required)):
    fields = db.query(models.Field).filter(models.Field.is_active == True).all()
    result = []
    for f in fields:
        semesters = [schemas.SemesterOut.model_validate(s) for s in f.semesters]
        result.append(schemas.FieldWithSemesters(
            id=f.id, name=f.name, description=f.description,
            is_active=f.is_active, semesters=semesters
        ))
    return result


@router.get("/subjects/{semester_id}", response_model=List[schemas.SubjectWithQuestions])
def get_subjects(semester_id: int, db: Session = Depends(get_db), _=Depends(teacher_required)):
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
def create_subject(data: schemas.SubjectCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    sem = db.query(models.Semester).filter(models.Semester.id == data.semester_id).first()
    if not sem:
        raise HTTPException(status_code=404, detail="Semester not found")
    subj = models.Subject(name=data.name, code=data.code, semester_id=data.semester_id, created_by=user.id)
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


@router.get("/assigned-subjects", response_model=List[schemas.SubjectOut])
def get_assigned_subjects(db: Session = Depends(get_db), user=Depends(teacher_required)):
    subject_ids = _teacher_subject_ids(db, user)
    if not subject_ids:
        return []
    return db.query(models.Subject).filter(models.Subject.id.in_(subject_ids)).all()


@router.delete("/subjects/{subj_id}")
def delete_subject(subj_id: int, db: Session = Depends(get_db), user=Depends(teacher_required)):
    subj = db.query(models.Subject).filter(models.Subject.id == subj_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subj.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only delete subjects you created")
    db.delete(subj)
    db.commit()
    return {"detail": "Deleted"}


# ── Question Management ──
@router.post("/questions", response_model=schemas.QuestionOut)
def create_question(data: schemas.QuestionCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, data.subject_id)
    subj = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
    q = models.Question(**data.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.put("/questions/{q_id}", response_model=schemas.QuestionOut)
def update_question(q_id: int, data: schemas.QuestionCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    q = db.query(models.Question).filter(models.Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    _ensure_subject_access(db, user, q.subject_id)
    for key, value in data.model_dump().items():
        setattr(q, key, value)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/questions/{q_id}")
def delete_question(q_id: int, db: Session = Depends(get_db), user=Depends(teacher_required)):
    q = db.query(models.Question).filter(models.Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    _ensure_subject_access(db, user, q.subject_id)
    db.delete(q)
    db.commit()
    return {"detail": "Deleted"}


# ── View Student Assessments ──
@router.get("/students")
def get_student_assessments(db: Session = Depends(get_db), user=Depends(teacher_required)):
    subject_ids = _teacher_subject_ids(db, user)
    if subject_ids:
        enrollments = (
            db.query(models.Enrollment)
            .filter(models.Enrollment.subject_id.in_(subject_ids), models.Enrollment.status == "active")
            .all()
        )
        rows = [serialize_prediction(db, e.student_id, e.subject_id) for e in enrollments]
        return sorted(rows, key=lambda row: row["risk_score"], reverse=True)

    assessments = (
        db.query(models.Assessment)
        .order_by(models.Assessment.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": a.id,
            "student_name": a.student.name,
            "student_email": a.student.email,
            "subject_name": a.subject.name,
            "risk_score": round(a.risk_score, 1),
            "risk_level": a.risk_level,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assessments
    ]


@router.get("/subjects/{subject_id}/students", response_model=List[schemas.RiskPredictionOut])
def get_subject_students(subject_id: int, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, subject_id)
    enrollments = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.subject_id == subject_id, models.Enrollment.status == "active")
        .all()
    )
    return [serialize_prediction(db, e.student_id, e.subject_id) for e in enrollments]


@router.post("/performance/attendance")
def record_attendance(data: schemas.AttendanceRecordCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, data.subject_id)
    _ensure_student(db, data.student_id)
    if data.attended_classes > data.total_classes:
        raise HTTPException(status_code=400, detail="Attended classes cannot exceed total classes")
    ensure_enrollment(db, data.student_id, data.subject_id)
    record = models.AttendanceRecord(**data.model_dump(), recorded_by=user.id)
    db.add(record)
    return _record_response(db, record, data.student_id, data.subject_id)


@router.post("/performance/assignments")
def record_assignment(data: schemas.AssignmentRecordCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, data.subject_id)
    _ensure_student(db, data.student_id)
    if data.score is not None and data.score > data.max_score:
        raise HTTPException(status_code=400, detail="Score cannot exceed max score")
    ensure_enrollment(db, data.student_id, data.subject_id)
    record = models.AssignmentRecord(**data.model_dump(), recorded_by=user.id)
    db.add(record)
    return _record_response(db, record, data.student_id, data.subject_id)


@router.post("/performance/internals")
def record_internal_score(data: schemas.InternalExamScoreCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, data.subject_id)
    _ensure_student(db, data.student_id)
    if data.score > data.max_score:
        raise HTTPException(status_code=400, detail="Score cannot exceed max score")
    ensure_enrollment(db, data.student_id, data.subject_id)
    record = models.InternalExamScore(**data.model_dump(), recorded_by=user.id)
    db.add(record)
    return _record_response(db, record, data.student_id, data.subject_id)


@router.post("/performance/practicals")
def record_practical_score(data: schemas.PracticalScoreCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, data.subject_id)
    _ensure_student(db, data.student_id)
    if data.score > data.max_score:
        raise HTTPException(status_code=400, detail="Score cannot exceed max score")
    ensure_enrollment(db, data.student_id, data.subject_id)
    record = models.PracticalScore(**data.model_dump(), recorded_by=user.id)
    db.add(record)
    return _record_response(db, record, data.student_id, data.subject_id)


@router.post("/interventions", response_model=schemas.InterventionOut)
def create_intervention(data: schemas.InterventionCreate, db: Session = Depends(get_db), user=Depends(teacher_required)):
    _ensure_subject_access(db, user, data.subject_id)
    _ensure_student(db, data.student_id)
    ensure_enrollment(db, data.student_id, data.subject_id)
    intervention = models.Intervention(**data.model_dump(), teacher_id=user.id)
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    
    from app.services.email_service import send_intervention_email
    student = db.query(models.User).filter(models.User.id == data.student_id).first()
    if student:
        send_intervention_email(student.email, student.name, intervention.title)
        
    return intervention


@router.get("/interventions", response_model=List[schemas.InterventionOut])
def list_interventions(db: Session = Depends(get_db), user=Depends(teacher_required)):
    subject_ids = _teacher_subject_ids(db, user)
    if not subject_ids:
        return []
    return (
        db.query(models.Intervention)
        .filter(models.Intervention.subject_id.in_(subject_ids))
        .order_by(models.Intervention.created_at.desc())
        .all()
    )


@router.put("/interventions/{intervention_id}", response_model=schemas.InterventionOut)
def update_intervention(
    intervention_id: int,
    data: schemas.InterventionUpdate,
    db: Session = Depends(get_db),
    user=Depends(teacher_required),
):
    intervention = db.query(models.Intervention).filter(models.Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    _ensure_subject_access(db, user, intervention.subject_id)
    if user.role != "admin" and intervention.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Only the assigned teacher can update this intervention")

    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(intervention, key, value)
    if updates.get("status") == "completed" and not intervention.completed_at:
        intervention.completed_at = datetime.now(timezone.utc)
    intervention.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(intervention)
    return intervention


# ── Bulk Import ──
@router.post("/performance/bulk-import")
async def bulk_import_performance(
    subject_id: int = Form(...),
    record_type: str = Form(...),
    title: str = Form(None),
    exam_name: str = Form(None),
    max_score: float = Form(100.0),
    total_classes: int = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(teacher_required),
):
    _ensure_subject_access(db, user, subject_id)
    
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded CSV")
    
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty CSV file")
        
    expected_cols = ["student_id"]
    if record_type == "attendance":
        expected_cols.append("attended_classes")
        if not total_classes and "total_classes" not in reader.fieldnames:
            raise HTTPException(status_code=400, detail="Missing total_classes column or form field")
    else:
        expected_cols.append("score")
        
    for col in expected_cols:
        if col not in reader.fieldnames:
            raise HTTPException(status_code=400, detail=f"Missing required CSV column: {col}. Found columns: {', '.join(reader.fieldnames)}")
            
    success_count = 0
    errors = []
    
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.subject_id == subject_id).all()
    enrolled_student_ids = [e.student_id for e in enrollments]
    students = db.query(models.User).filter(models.User.id.in_(enrolled_student_ids)).all()
    
    student_map = {s.student_id.strip(): s.id for s in students if s.student_id}
    for s in students:
        student_map[str(s.id)] = s.id

    records_to_add = []
    student_db_ids_updated = set()
    
    for row_num, row in enumerate(reader, start=2):
        s_id_raw = row.get("student_id", "").strip()
        if not s_id_raw:
            continue
            
        db_student_id = student_map.get(s_id_raw)
        if not db_student_id:
            errors.append(f"Row {row_num}: Student ID '{s_id_raw}' not found or not enrolled in this subject.")
            continue
            
        try:
            if record_type == "attendance":
                attended = int(row["attended_classes"])
                total = int(row.get("total_classes") or total_classes)
                if attended > total:
                    raise ValueError("Attended classes cannot exceed total classes")
                record = models.AttendanceRecord(
                    student_id=db_student_id,
                    subject_id=subject_id,
                    attended_classes=attended,
                    total_classes=total,
                    recorded_by=user.id
                )
            elif record_type == "assignment":
                score_str = row.get("score", "").strip()
                submitted = bool(score_str)
                score = float(score_str) if submitted else None
                record = models.AssignmentRecord(
                    student_id=db_student_id,
                    subject_id=subject_id,
                    title=title or "Bulk Assignment",
                    submitted=submitted,
                    score=score,
                    max_score=max_score,
                    recorded_by=user.id
                )
            elif record_type == "internal":
                score = float(row["score"])
                record = models.InternalExamScore(
                    student_id=db_student_id,
                    subject_id=subject_id,
                    exam_name=exam_name or "Bulk Internal",
                    score=score,
                    max_score=max_score,
                    recorded_by=user.id
                )
            elif record_type == "practical":
                score = float(row["score"])
                record = models.PracticalScore(
                    student_id=db_student_id,
                    subject_id=subject_id,
                    title=title or "Bulk Practical",
                    score=score,
                    max_score=max_score,
                    recorded_by=user.id
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid record type")
                
            records_to_add.append(record)
            student_db_ids_updated.add(db_student_id)
            success_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: Invalid data format - {str(e)}")
            
    if records_to_add:
        db.bulk_save_objects(records_to_add)
        db.commit()
        
        for student_id in student_db_ids_updated:
            compute_and_store_risk(db, student_id, subject_id)
        db.commit()
        
    return {
        "success_count": success_count,
        "errors": errors,
        "message": f"Successfully imported {success_count} records. {len(errors)} errors found."
    }
